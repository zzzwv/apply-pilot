"""Local-first, non-persisting company intelligence orchestration."""

import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterable
from time import monotonic
from typing import Any

from app.company_intelligence.cache import CompanyIntelligenceCache
from app.company_intelligence.kimi_two_stage import KimiTwoStageCompanyProvider
from app.company_intelligence.links import HttpxLinkValidator, discover_recruitment_links
from app.company_intelligence.providers import (
    CompanySearchProvider,
    ProviderError,
    ProviderErrorCode,
)
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

logger = logging.getLogger(__name__)

_PROVIDER_SAFETY_RESERVE_SECONDS = 2.0


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
        overall_timeout_seconds: float = 60,
        provider_safety_reserve_seconds: float = _PROVIDER_SAFETY_RESERVE_SECONDS,
    ) -> None:
        settings = settings or get_settings()
        if repository is None:
            if session is None:
                raise ValueError("session or repository is required")
            repository = CompanyRepository(session)
        self.companies = repository
        self.providers = list(providers or [KimiTwoStageCompanyProvider(settings)])
        self.cache = cache or CompanyIntelligenceCache(
            redis=get_redis(),
            ttl_seconds=settings.company_intelligence_cache_ttl_seconds,
            rate_limit_max_requests=settings.company_intelligence_rate_limit_max_requests,
            rate_limit_window_seconds=settings.company_intelligence_rate_limit_window_seconds,
        )
        self.link_validator = link_validator if link_validator is not None else HttpxLinkValidator()
        self.overall_timeout_seconds = overall_timeout_seconds
        self.provider_safety_reserve_seconds = provider_safety_reserve_seconds

    async def search_company(
        self, request: CompanyIntelligenceSearchRequest, *, actor_id: object
    ) -> CompanyIntelligenceSearchResult:
        started_at = monotonic()
        name = request.company_name
        try:
            local = await self._within_budget(
                lambda: self.companies.find_by_name_or_alias(name), started_at
            )
        except asyncio.TimeoutError:
            return self._partial("local company lookup timed out")
        if local is not None:
            candidate = self._local_candidate(local)
            return CompanyIntelligenceSearchResult(
                company=candidate,
                recruitment_links=candidate.recruitment_links,
            )

        if not request.force_refresh:
            try:
                cached = await self._within_budget(lambda: self.cache.get(name), started_at)
            except asyncio.TimeoutError:
                return self._partial("company intelligence search timed out")
            if cached is not None:
                return cached

        try:
            allowed = await self._within_budget(
                lambda: self.cache.allow_request(actor_id), started_at
            )
        except asyncio.TimeoutError:
            return self._partial("company intelligence search timed out")
        if not allowed:
            return self._partial(
                "company intelligence rate limit reached; enter company details manually"
            )

        try:
            lock_token = await self._acquire_lock_with_budget(name, started_at)
        except asyncio.TimeoutError:
            return self._partial("company intelligence search timed out")
        if lock_token is None:
            try:
                cached = await self._within_budget(
                    lambda: self.cache.wait_for_result(name, self._remaining(started_at)),
                    started_at,
                )
            except asyncio.TimeoutError:
                return self._partial("company intelligence search timed out")
            if cached is not None:
                return cached
            return self._partial("company intelligence search is already in progress")

        try:
            if not request.force_refresh:
                try:
                    cached = await self._within_budget(
                        lambda: self.cache.get(name), started_at
                    )
                except asyncio.TimeoutError:
                    return self._partial("company intelligence search timed out")
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
            if self._remaining(started_at) > 0:
                try:
                    await self._within_budget(lambda: self.cache.set(name, result), started_at)
                except asyncio.TimeoutError:
                    result.warnings.append("company intelligence cache write was skipped")
                    result.partial = True
            return result
        finally:
            await self._release_lock_with_budget(name, lock_token, started_at)

    async def _search_providers(
        self, name: str, started_at: float
    ) -> tuple[list[CompanyCandidate], list[str]]:
        provider_budget = self._remaining(started_at) - self.provider_safety_reserve_seconds
        if provider_budget <= 0:
            return [], ["company intelligence provider budget was exhausted"]
        provider_deadline = monotonic() + provider_budget
        tasks = [
            asyncio.create_task(provider.search(name, deadline=provider_deadline))
            for provider in self.providers
        ]
        if not tasks:
            return [], ["company intelligence provider is not configured"]
        done, pending = await asyncio.wait(tasks, timeout=provider_budget)
        warnings: list[str] = []
        if pending:
            await self._cancel_pending(pending, started_at)
            logger.warning(
                "KIMI_PROVIDER_CANCELLED_BY_SERVICE_TIMEOUT",
                extra={"provider_task_count": len(pending)},
            )
            warnings.append("company intelligence provider search timed out")

        candidates: list[CompanyCandidate] = []
        for task in done:
            try:
                response = task.result()
            except ProviderError as error:
                logger.warning(
                    "company intelligence provider failure: %s diagnostic=%s",
                    error.code,
                    error.diagnostic,
                )
                warnings.append(self._safe_provider_warning(error))
            except Exception:
                warnings.append("company intelligence provider is temporarily unavailable")
            else:
                candidates.append(response)
        return candidates, warnings

    @staticmethod
    def _safe_provider_warning(error: ProviderError) -> str:
        if error.code is ProviderErrorCode.RATE_LIMITED:
            return "company intelligence provider rate limit reached"
        if error.code is ProviderErrorCode.PROVIDER_BUDGET_EXHAUSTED:
            return "company intelligence provider budget was exhausted"
        return "company intelligence provider is temporarily unavailable"

    async def _verify(
        self, candidate: CompanyCandidate, started_at: float
    ) -> tuple[CompanyCandidate, list[str]]:
        if self.link_validator is None:
            return candidate, []
        links = list(candidate.recruitment_links)
        warnings: list[str] = []
        if candidate.official_website is not None:
            try:
                discovered = await self._within_budget(
                    lambda: discover_recruitment_links(
                        homepage_url=candidate.official_website,
                        company_name=candidate.company_name,
                        validator=self.link_validator,
                    ),
                    started_at,
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
            await self._cancel_pending(pending, started_at)
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
                continue
            channel = getattr(link, "channel", "third_party")
            channel_type = channel.value if hasattr(channel, "value") else str(channel)
            link_type = getattr(link, "link_type", None)
            type_value = link_type.value if hasattr(link_type, "value") else str(link_type)
            links.append(
                RecruitmentLinkCandidate(
                    title=getattr(link, "source_title", None) or link.url,
                    url=link.url,
                    channel_type=channel_type,
                    claimed_official=type_value == "official",
                    source_url=getattr(link, "source_url", None),
                    evidence=getattr(link, "source", None),
                    verification_status=(
                        getattr(link, "verification_status", None)
                        or VerificationStatus.UNVERIFIED
                    ),
                    valid_status=getattr(link, "valid_status", None) or "unknown",
                    http_status=getattr(link, "http_status", None),
                    final_url=getattr(link, "final_url", None),
                )
            )
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

    async def _within_budget(
        self,
        operation: Callable[[], Awaitable[Any]],
        started_at: float,
    ) -> Any:
        remaining = self._remaining(started_at)
        if remaining <= 0:
            raise asyncio.TimeoutError
        task = asyncio.create_task(operation())
        done, _ = await asyncio.wait({task}, timeout=remaining)
        if task not in done:
            task.cancel()
            self._drain(task)
            raise asyncio.TimeoutError
        return task.result()

    async def _cancel_pending(
        self, pending: set[asyncio.Task[Any]], started_at: float
    ) -> None:
        del started_at
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    async def _acquire_lock_with_budget(self, name: str, started_at: float) -> str | None:
        remaining = self._remaining(started_at)
        if remaining <= 0:
            raise asyncio.TimeoutError
        task = asyncio.create_task(self.cache.acquire_lock(name))
        try:
            done, _ = await asyncio.wait({task}, timeout=remaining)
        except BaseException:
            task.cancel()
            self._release_late_lock(name, task)
            raise
        if task in done:
            return task.result()
        task.cancel()
        self._release_late_lock(name, task)
        raise asyncio.TimeoutError

    def _release_late_lock(self, name: str, task: asyncio.Task[str | None]) -> None:
        def release_if_acquired(done: asyncio.Task[str | None]) -> None:
            if done.cancelled():
                return
            try:
                token = done.result()
            except Exception:
                return
            if token is not None:
                cleanup = asyncio.create_task(self.cache.release_lock(name, token))
                self._drain(cleanup)

        task.add_done_callback(release_if_acquired)
        self._drain(task)

    async def _release_lock_with_budget(
        self, name: str, token: str, started_at: float
    ) -> None:
        task = asyncio.create_task(self.cache.release_lock(name, token))
        self._drain(task)
        remaining = self._remaining(started_at)
        if remaining <= 0:
            return
        try:
            await asyncio.wait_for(asyncio.shield(task), remaining)
        except asyncio.TimeoutError:
            return

    @staticmethod
    def _drain(task: asyncio.Task[Any]) -> None:
        def consume(done: asyncio.Task[Any]) -> None:
            if not done.cancelled():
                try:
                    done.exception()
                except Exception:
                    pass

        task.add_done_callback(consume)

    @staticmethod
    def _partial(warning: str) -> CompanyIntelligenceSearchResult:
        return CompanyIntelligenceSearchResult(partial=True, warnings=[warning])
