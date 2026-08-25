import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest

from app.company_intelligence.providers import ProviderError, ProviderErrorCode
from app.company_intelligence.schemas import (
    CandidateSource,
    CompanyCandidate,
    CompanyIntelligenceSearchRequest,
)


def candidate(
    name: str = "Acme Corporation",
    *,
    website: str | None = "https://www.acme.example",
    industry: str | None = "Software",
) -> CompanyCandidate:
    return CompanyCandidate(
        company_name=name,
        official_website=website,
        industry=industry,
        sources=[
            CandidateSource(
                url="https://www.acme.example/about",
                title="About Acme",
                source_type="official_site",
                provider="test",
                retrieved_at=datetime(2026, 8, 25, tzinfo=UTC),
            )
        ],
    )


@dataclass
class LocalCompany:
    full_name: str
    short_name: str | None = None
    industry: str | None = None
    nature: str | None = None
    size: str | None = None
    official_website: str | None = None
    business_description: str | None = None
    recruitment_links: list[object] = field(default_factory=list)


class LocalRepository:
    def __init__(self, company: LocalCompany | None = None) -> None:
        self.company = company
        self.seen_names: list[str] = []

    async def find_by_name_or_alias(self, normalized_name: str) -> LocalCompany | None:
        self.seen_names.append(normalized_name)
        return self.company


class SlowLocalRepository(LocalRepository):
    async def find_by_name_or_alias(self, normalized_name: str) -> LocalCompany | None:
        await asyncio.sleep(0.05)
        return await super().find_by_name_or_alias(normalized_name)


class StaticProvider:
    def __init__(self, result: CompanyCandidate | Exception) -> None:
        self.result = result
        self.calls = 0

    async def search(self, company_name: str) -> CompanyCandidate:
        del company_name
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class BlockingProvider(StaticProvider):
    def __init__(self, result: CompanyCandidate) -> None:
        super().__init__(result)
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def search(self, company_name: str) -> CompanyCandidate:
        del company_name
        self.calls += 1
        self.started.set()
        await self.release.wait()
        assert isinstance(self.result, CompanyCandidate)
        return self.result


class FailingRedis:
    async def get(self, key: str) -> None:
        del key
        raise ConnectionError("redis unavailable")

    async def set(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise ConnectionError("redis unavailable")

    async def delete(self, key: str) -> None:
        del key
        raise ConnectionError("redis unavailable")


class NoNetworkValidator:
    async def validate(self, url: str):
        del url
        from app.company_intelligence.links import ValidatedLink
        from app.models.enums import LinkStatus

        return ValidatedLink(LinkStatus.UNKNOWN, None, "https://www.acme.example", "not fetched")


def service(
    repository: LocalRepository,
    providers: list[StaticProvider],
    *,
    cache=None,
    rate_limit: int = 10,
    overall_timeout_seconds: float = 10,
):
    from app.company_intelligence.cache import CompanyIntelligenceCache
    from app.services.company_intelligence_service import CompanyIntelligenceService

    return CompanyIntelligenceService(
        repository=repository,
        providers=providers,
        cache=cache
        or CompanyIntelligenceCache(
            redis=None,
            ttl_seconds=60,
            rate_limit_max_requests=rate_limit,
            rate_limit_window_seconds=60,
        ),
        link_validator=NoNetworkValidator(),
        overall_timeout_seconds=overall_timeout_seconds,
    )


@pytest.mark.asyncio
async def test_exact_local_match_returns_candidate_without_calling_kimi() -> None:
    """Protects existing company records from unnecessary provider traffic."""
    provider = StaticProvider(candidate())
    result = await service(
        LocalRepository(LocalCompany(full_name="Acme Corporation", industry="Local software")),
        [provider],
    ).search_company(CompanyIntelligenceSearchRequest(company_name=" Acme Corporation "))

    assert result.partial is False
    assert result.company is not None
    assert result.company.company_name == "acme corporation"
    assert result.company.industry == "Local software"
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_alias_local_match_returns_company_without_calling_kimi() -> None:
    """Protects aliases from bypassing the local-first lookup policy."""
    provider = StaticProvider(candidate())
    repository = LocalRepository(LocalCompany(full_name="Acme Corporation"))
    result = await service(repository, [provider]).search_company(
        CompanyIntelligenceSearchRequest(company_name="Acme")
    )

    assert repository.seen_names == ["acme"]
    assert result.company is not None
    assert result.company.company_name == "acme corporation"
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_slow_local_lookup_uses_the_overall_budget_before_remote_work() -> None:
    """Protects the ten-second budget from an unbounded local database stage."""
    provider = StaticProvider(candidate())

    result = await service(
        SlowLocalRepository(), [provider], overall_timeout_seconds=0.01
    ).search_company(CompanyIntelligenceSearchRequest(company_name="Acme Corporation"))

    assert result.company is None
    assert result.partial is True
    assert result.warnings == ["local company lookup timed out"]
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_cache_hit_avoids_provider_and_redis_loss_uses_memory_cache() -> None:
    """Protects normalized repeated searches when Redis is temporarily unavailable."""
    from app.company_intelligence.cache import CompanyIntelligenceCache

    provider = StaticProvider(candidate())
    cache = CompanyIntelligenceCache(
        redis=FailingRedis(),
        ttl_seconds=60,
        rate_limit_max_requests=10,
        rate_limit_window_seconds=60,
    )
    intelligence = service(LocalRepository(), [provider], cache=cache)

    first = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="Acme Corporation")
    )
    second = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="  acme corporation  ")
    )

    assert first.company is not None
    assert second.company is not None
    assert second.company.company_name == "acme corporation"
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_force_refresh_bypasses_cache_but_still_runs_remote_path() -> None:
    """Protects refresh from returning stale data while retaining remote safeguards."""
    provider = StaticProvider(candidate())
    intelligence = service(LocalRepository(), [provider])

    await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="Acme Corporation")
    )
    refreshed = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="Acme Corporation", force_refresh=True)
    )

    assert refreshed.company is not None
    assert provider.calls == 2


@pytest.mark.asyncio
async def test_concurrent_requests_coalesce_behind_one_cache_lock() -> None:
    """Protects a cache miss from multiplying the same Kimi request."""
    provider = BlockingProvider(candidate())
    intelligence = service(LocalRepository(), [provider])
    request = CompanyIntelligenceSearchRequest(company_name="Acme Corporation")

    first = asyncio.create_task(intelligence.search_company(request))
    await provider.started.wait()
    second = asyncio.create_task(intelligence.search_company(request))
    await asyncio.sleep(0)
    provider.release.set()
    first_result, second_result = await asyncio.gather(first, second)

    assert first_result.company is not None
    assert second_result.company is not None
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_rate_limit_returns_manual_fallback_without_provider_call() -> None:
    """Protects the provider boundary from a forced refresh bypassing rate limits."""
    provider = StaticProvider(candidate())
    intelligence = service(LocalRepository(), [provider], rate_limit=1)

    first = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="Acme Corporation")
    )
    limited = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="Acme Corporation", force_refresh=True)
    )

    assert first.company is not None
    assert limited.company is None
    assert limited.partial is True
    assert limited.allow_manual_input is True
    assert "rate limit" in limited.warnings[0]
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_partial_kimi_failure_keeps_successful_candidate_visible() -> None:
    """Protects a usable provider result from an independent provider outage."""
    successful = StaticProvider(candidate())
    unavailable = StaticProvider(
        ProviderError(
            ProviderErrorCode.TRANSIENT_FAILURE,
            "Kimi provider is temporarily unavailable",
        )
    )

    result = await service(LocalRepository(), [successful, unavailable]).search_company(
        CompanyIntelligenceSearchRequest(company_name="Acme Corporation")
    )

    assert result.company is not None
    assert result.partial is True
    assert "temporarily unavailable" in result.warnings[0]


@pytest.mark.asyncio
async def test_conflicting_provider_candidates_remain_visible_as_partial_conflict() -> None:
    """Protects a disagreement over company identity from being silently persisted as truth."""
    first = StaticProvider(candidate(website="https://one.acme.example"))
    second = StaticProvider(candidate(website="https://two.acme.example"))

    result = await service(LocalRepository(), [first, second]).search_company(
        CompanyIntelligenceSearchRequest(company_name="Acme Corporation")
    )

    assert result.company is None
    assert result.partial is True
    assert "conflict" in result.warnings[0]
