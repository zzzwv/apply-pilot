"""Local-first, non-persisting company intelligence orchestration."""

import asyncio
from collections.abc import Iterable
from time import monotonic
from typing import Any

from app.company_intelligence.cache import CompanyIntelligenceCache
from app.company_intelligence.kimi import KimiCompanySearchProvider
from app.company_intelligence.links import HttpxLinkValidator, discover_recruitment_links
from app.company_intelligence.providers import CompanySearchProvider, ProviderError
from app.company_intelligence.schemas import (
    CandidateSource,
    CompanyCandidate,
    CompanyIntelligenceSearchRequest,
    CompanyIntelligenceSearchResult,
    RecruitmentLinkCandidate,
)
from app.company_intelligence.verification import rank_recruitment_links, verify_recruitment_link
from app.core.config import Settings, get_settings
from app.core.redis import get_redis
from app.models.enums import VerificationStatus
from app.repositories.company import CompanyRepository


class CompanyIntelligenceService:
    """Return editable candidates only; this service never writes company records."""

    def __init__(
        self,
        session: Any | None = None,
        *,
        repository: CompanyRepository | Any | None = None,
        providers: Iterable[CompanySearchProvider] | None = None,
        cache: CompanyIntelligenceCache | None = None,
        link_validator: HttpxLinkValidator | None = None,
        settings: Settings | None = None,
        overall_timeout_seconds: float = 10,
    ) -> None:
        settings = settings or get_settings()
        if repository is None:
            if session is None:
                raise ValueError("session or repository is required")
            repository = CompanyRepository(session)
        self.companies = repository
        self.providers = list(providers or [KimiCompanySearchProvider(settings)])
        self.cache = cache or CompanyIntelligenceCache(
            redis=get_redis(),
            ttl_seconds=settings.company_intelligence_cache_ttl_seconds,
            rate_limit_max_requests=settings.company_intelligence_rate_limit_max_requests,
            rate_limit_window_seconds=settings.company_intelligence_rate_limit_window_seconds,
        )
        self.link_validator = link_validator if link_validator is not None else HttpxLinkValidator()
        self.overall_timeout_seconds = overall_timeout_seconds

    async def search_company(
        self, request: CompanyIntelligenceSearchRequest
    ) -> CompanyIntelligenceSearchResult:
        started_at = monotonic()
        name = request.company_name
        try:
            local = await asyncio.wait_for(
                self.companies.find_by_name_or_alias(name),
                timeout=self._remaining(started_at),
            )
        except asyncio.TimeoutError:
            return self._partial("local company lookup timed out")
        if local is not None:
            return CompanyIntelligenceSearchResult(company=self._local_candidate(local))

        if not request.force_refresh:
            cached = await self.cache.get(name)
            if cached is not None:
                return cached

        if not await self.cache.allow_request(name):
            return self._partial(
                "company intelligence rate limit reached; enter company details manually"
            )

        lock_token = await self.cache.acquire_lock(name)
        if lock_token is None:
            cached = await self.cache.wait_for_result(name, self._remaining(started_at))
            if cached is not None:
                return cached
            return self._partial("company intelligence search is already in progress")

        try:
            if not request.force_refresh:
                cached = await self.cache.get(name)
                if cached is not None:
                    return cached

            candidates, warnings = await self._search_providers(name, started_at)
            merged, conflicts = self._merge_candidates(candidates)
            warnings.extend(conflicts)
            if merged is None:
                return CompanyIntelligenceSearchResult(
                    recruitment_links=self._merged_links(candidates),
                    sources=self._merged_sources(candidates),
                    partial=True,
                    warnings=warnings or ["no company intelligence candidate was returned"],
                )

            verified, verification_warnings = await self._verify(merged, started_at)
            warnings.extend(verification_warnings)
            result = CompanyIntelligenceSearchResult(
                company=verified,
                recruitment_links=verified.recruitment_links,
                sources=verified.sources,
                partial=bool(warnings),
                warnings=warnings,
            )
            await self.cache.set(name, result)
            return result
        finally:
            await self.cache.release_lock(name, lock_token)

    async def _search_providers(
        self, name: str, started_at: float
    ) -> tuple[list[CompanyCandidate], list[str]]:
        tasks = [asyncio.create_task(provider.search(name)) for provider in self.providers]
        if not tasks:
            return [], ["company intelligence provider is not configured"]
        done, pending = await asyncio.wait(tasks, timeout=self._remaining(started_at))
        warnings: list[str] = []
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
            warnings.append("company intelligence provider search timed out")

        candidates: list[CompanyCandidate] = []
        for task in done:
            try:
                response = task.result()
            except ProviderError as error:
                warnings.append(str(error))
            except Exception:
                warnings.append("company intelligence provider is temporarily unavailable")
            else:
                candidates.append(response)
        return candidates, warnings

    async def _verify(
        self, candidate: CompanyCandidate, started_at: float
    ) -> tuple[CompanyCandidate, list[str]]:
        if self.link_validator is None:
            return candidate, []
        links = list(candidate.recruitment_links)
        warnings: list[str] = []
        if candidate.official_website is not None:
            try:
                discovered = await asyncio.wait_for(
                    discover_recruitment_links(
                        homepage_url=candidate.official_website,
                        company_name=candidate.company_name,
                        validator=self.link_validator,
                    ),
                    timeout=self._remaining(started_at),
                )
                links.extend(discovered)
            except Exception:
                warnings.append("recruitment link discovery was incomplete")

        unique = {link.url: link for link in links}
        tasks = [
            asyncio.create_task(
                verify_recruitment_link(
                    candidate=link,
                    company_name=candidate.company_name,
                    official_website=candidate.official_website,
                    validator=self.link_validator,
                )
            )
            for link in unique.values()
        ]
        if not tasks:
            return candidate, warnings
        done, pending = await asyncio.wait(tasks, timeout=self._remaining(started_at))
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
            warnings.append("recruitment link verification was incomplete")
        verified: list[RecruitmentLinkCandidate] = []
        for task in done:
            try:
                verified.append(task.result())
            except Exception:
                warnings.append("recruitment link verification was incomplete")
        return (
            candidate.model_copy(
                update={"recruitment_links": rank_recruitment_links(verified)}
            ),
            warnings,
        )

    @staticmethod
    def _merge_candidates(
        candidates: list[CompanyCandidate],
    ) -> tuple[CompanyCandidate | None, list[str]]:
        if not candidates:
            return None, []
        first = candidates[0]
        conflict_fields: list[str] = []
        for field in (
            "company_name",
            "short_name",
            "industry",
            "company_nature",
            "company_size",
            "official_website",
            "description",
        ):
            values = {
                getattr(candidate, field)
                for candidate in candidates
                if getattr(candidate, field)
            }
            if len(values) > 1:
                conflict_fields.append(field)
        if conflict_fields:
            return None, ["conflicting provider candidates: " + ", ".join(conflict_fields)]
        return first.model_copy(
            update={
                "recruitment_links": CompanyIntelligenceService._merged_links(candidates),
                "sources": CompanyIntelligenceService._merged_sources(candidates),
            }
        ), []

    @staticmethod
    def _merged_links(candidates: list[CompanyCandidate]) -> list[RecruitmentLinkCandidate]:
        by_url: dict[str, RecruitmentLinkCandidate] = {}
        for candidate in candidates:
            for link in candidate.recruitment_links:
                by_url.setdefault(link.url, link)
        return rank_recruitment_links(list(by_url.values()))

    @staticmethod
    def _merged_sources(candidates: list[CompanyCandidate]) -> list[CandidateSource]:
        by_url: dict[str, CandidateSource] = {}
        for candidate in candidates:
            for source in candidate.sources:
                by_url.setdefault(source.url, source)
        return list(by_url.values())

    @staticmethod
    def _local_candidate(company: Any) -> CompanyCandidate:
        links: list[RecruitmentLinkCandidate] = []
        for link in getattr(company, "recruitment_links", []):
            if isinstance(link, RecruitmentLinkCandidate):
                links.append(link)
        return CompanyCandidate(
            company_name=company.full_name,
            short_name=getattr(company, "short_name", None),
            industry=getattr(company, "industry", None),
            company_nature=getattr(company, "nature", None),
            company_size=getattr(company, "size", None),
            official_website=getattr(company, "official_website", None),
            description=getattr(company, "business_description", None),
            recruitment_links=links,
            verification_status=VerificationStatus.VERIFIED,
        )

    def _remaining(self, started_at: float) -> float:
        return max(0.0, self.overall_timeout_seconds - (monotonic() - started_at))

    @staticmethod
    def _partial(warning: str) -> CompanyIntelligenceSearchResult:
        return CompanyIntelligenceSearchResult(partial=True, warnings=[warning])
