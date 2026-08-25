import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import monotonic

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


class ScalarResult:
    def __init__(self, first: object | None, all_values: list[object]) -> None:
        self._first = first
        self._all_values = all_values

    def scalars(self) -> "ScalarResult":
        return self

    def first(self) -> object | None:
        return self._first

    def all(self) -> list[object]:
        return self._all_values


class NormalizationFallbackSession:
    def __init__(self, company: object) -> None:
        self.company = company
        self.executions = 0

    async def execute(self, statement: object) -> ScalarResult:
        del statement
        self.executions += 1
        return ScalarResult(None, [self.company])


class StallingCache:
    async def get(self, normalized_name: str):
        del normalized_name
        await asyncio.sleep(0.05)
        return None

    async def allow_request(self, actor_id: object) -> bool:
        del actor_id
        return True

    async def acquire_lock(self, normalized_name: str) -> str:
        del normalized_name
        return "lock"

    async def release_lock(self, normalized_name: str, token: str) -> None:
        del normalized_name, token

    async def set(self, normalized_name: str, result: object) -> None:
        del normalized_name, result


class CancellationResistantLockCache(StallingCache):
    def __init__(self) -> None:
        self.released_tokens: list[str] = []
        self.released = asyncio.Event()

    async def get(self, normalized_name: str):
        del normalized_name
        return None

    async def acquire_lock(self, normalized_name: str) -> str:
        del normalized_name
        try:
            await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            await asyncio.sleep(0)
        return "late-lock-token"

    async def release_lock(self, normalized_name: str, token: str) -> None:
        del normalized_name
        self.released_tokens.append(token)
        self.released.set()


class AtomicRateRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    async def eval(self, script: str, key_count: int, *args: object) -> int:
        self.calls.append((script, args))
        assert key_count == 1
        return 1


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
    ).search_company(
        CompanyIntelligenceSearchRequest(company_name=" Acme Corporation "),
        actor_id="local-exact-user",
    )

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
        CompanyIntelligenceSearchRequest(company_name="Acme"), actor_id="local-alias-user"
    )

    assert repository.seen_names == ["acme"]
    assert result.company is not None
    assert result.company.company_name == "acme corporation"
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_repository_normalization_fallback_matches_unicode_full_name_before_kimi() -> None:
    """Protects equivalent stored Unicode names from falling through to a remote search."""
    from app.models import Company
    from app.repositories.company import CompanyRepository
    from app.services.company_intelligence_service import CompanyIntelligenceService

    company = Company(full_name="ＡＣＭＥ　ＣＯＲＰＯＲＡＴＩＯＮ")
    session = NormalizationFallbackSession(company)
    provider = StaticProvider(candidate())
    intelligence = CompanyIntelligenceService(
        repository=CompanyRepository(session),
        providers=[provider],
        cache=StallingCache(),
        link_validator=NoNetworkValidator(),
    )

    result = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name=" AcMe   Corporation "),
        actor_id="user-normalized",
    )

    assert result.company is not None
    assert result.company.company_name == "acme corporation"
    assert session.executions == 2
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_slow_local_lookup_uses_the_overall_budget_before_remote_work() -> None:
    """Protects the ten-second budget from an unbounded local database stage."""
    provider = StaticProvider(candidate())

    result = await service(
        SlowLocalRepository(), [provider], overall_timeout_seconds=0.01
    ).search_company(
        CompanyIntelligenceSearchRequest(company_name="Acme Corporation"),
        actor_id="local-timeout-user",
    )

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
        CompanyIntelligenceSearchRequest(company_name="Cache Corporation"), actor_id="cache-user"
    )
    second = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="  cache corporation  "),
        actor_id="cache-user",
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
        CompanyIntelligenceSearchRequest(company_name="Refresh Corporation"),
        actor_id="refresh-user",
    )
    refreshed = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="Refresh Corporation", force_refresh=True),
        actor_id="refresh-user",
    )

    assert refreshed.company is not None
    assert provider.calls == 2


@pytest.mark.asyncio
async def test_concurrent_requests_coalesce_behind_one_cache_lock() -> None:
    """Protects a cache miss from multiplying the same Kimi request."""
    provider = BlockingProvider(candidate())
    intelligence = service(LocalRepository(), [provider])
    request = CompanyIntelligenceSearchRequest(company_name="Lock Corporation")

    first = asyncio.create_task(intelligence.search_company(request, actor_id="lock-user"))
    await provider.started.wait()
    second = asyncio.create_task(intelligence.search_company(request, actor_id="lock-user"))
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
        CompanyIntelligenceSearchRequest(company_name="Rate Corporation"), actor_id="rate-user"
    )
    limited = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="Rate Corporation", force_refresh=True),
        actor_id="rate-user",
    )

    assert first.company is not None
    assert limited.company is None
    assert limited.partial is True
    assert limited.allow_manual_input is True
    assert "rate limit" in limited.warnings[0]
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_rate_limit_isolated_by_actor_id() -> None:
    """Protects one user's Kimi budget from consuming another user's request quota."""
    provider = StaticProvider(candidate())
    intelligence = service(LocalRepository(), [provider], rate_limit=1)
    request = CompanyIntelligenceSearchRequest(company_name="Actor Rate Corporation")

    await intelligence.search_company(request, actor_id="alice")
    alice_limited = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="Actor Rate Corporation", force_refresh=True),
        actor_id="alice",
    )
    bob = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="Actor Rate Corporation", force_refresh=True),
        actor_id="bob",
    )

    assert alice_limited.company is None
    assert bob.company is not None
    assert provider.calls == 2


@pytest.mark.asyncio
async def test_default_memory_state_coalesces_cache_instances_during_redis_loss() -> None:
    """Protects process-local fallback locks from fragmenting across service instances."""
    from app.company_intelligence.cache import CompanyIntelligenceCache

    first = CompanyIntelligenceCache(
        redis=None,
        ttl_seconds=60,
        rate_limit_max_requests=10,
        rate_limit_window_seconds=60,
    )
    second = CompanyIntelligenceCache(
        redis=None,
        ttl_seconds=60,
        rate_limit_max_requests=10,
        rate_limit_window_seconds=60,
    )

    token = await first.acquire_lock("process-shared-default-state")

    assert token is not None
    assert await second.acquire_lock("process-shared-default-state") is None
    await first.release_lock("process-shared-default-state", token)


@pytest.mark.asyncio
async def test_cache_rate_increment_sets_expiry_in_one_redis_script() -> None:
    """Protects a Redis counter from becoming permanent between increment and expiry calls."""
    from app.company_intelligence.cache import CompanyIntelligenceCache

    redis = AtomicRateRedis()
    cache = CompanyIntelligenceCache(
        redis=redis,
        ttl_seconds=60,
        rate_limit_max_requests=10,
        rate_limit_window_seconds=60,
    )

    allowed = await cache.allow_request("atomic-rate-user")

    assert allowed is True
    assert len(redis.calls) == 1
    assert "expire" in redis.calls[0][0].casefold()


@pytest.mark.asyncio
async def test_cache_stage_cannot_extend_the_overall_deadline() -> None:
    """Protects a stalled cache client from stretching a ten-second search budget."""
    provider = StaticProvider(candidate())
    intelligence = service(
        LocalRepository(),
        [provider],
        cache=StallingCache(),
        overall_timeout_seconds=0.01,
    )
    started = monotonic()

    result = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="Acme Corporation"),
        actor_id="deadline-user",
    )

    assert monotonic() - started < 0.04
    assert result.company is None
    assert result.warnings == ["company intelligence search timed out"]
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_late_cancellation_resistant_lock_is_released_after_deadline() -> None:
    """Protects Redis from an orphaned lock when acquisition ignores cancellation briefly."""
    provider = StaticProvider(candidate())
    cache = CancellationResistantLockCache()
    intelligence = service(
        LocalRepository(),
        [provider],
        cache=cache,
        overall_timeout_seconds=0.01,
    )

    result = await intelligence.search_company(
        CompanyIntelligenceSearchRequest(company_name="Late Lock Corporation"),
        actor_id="late-lock-user",
    )
    await asyncio.wait_for(cache.released.wait(), timeout=0.1)

    assert result.company is None
    assert result.warnings == ["company intelligence search timed out"]
    assert cache.released_tokens == ["late-lock-token"]
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_local_orm_recruitment_link_is_returned_as_editable_candidate() -> None:
    """Protects saved recruitment links from disappearing in a local-first preview."""
    from app.models import RecruitmentLink
    from app.models.enums import RecruitmentChannel, RecruitmentLinkType

    link = RecruitmentLink(
        url="https://jobs.acme.example/campus",
        channel=RecruitmentChannel.OFFICIAL_CAMPUS,
        link_type=RecruitmentLinkType.OFFICIAL,
        source_title="Acme campus recruitment",
        source="local_record",
        source_url="https://www.acme.example/careers",
    )
    local = LocalCompany(full_name="Acme Corporation", recruitment_links=[link])

    result = await service(LocalRepository(local), [StaticProvider(candidate())]).search_company(
        CompanyIntelligenceSearchRequest(company_name="Acme Corporation"),
        actor_id="link-user",
    )

    assert result.company is not None
    assert [(item.url, item.channel_type, item.title) for item in result.recruitment_links] == [
        ("https://jobs.acme.example/campus", "official_campus", "Acme campus recruitment")
    ]


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
        CompanyIntelligenceSearchRequest(company_name="Partial Corporation"),
        actor_id="partial-user",
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
        CompanyIntelligenceSearchRequest(company_name="Conflict Corporation"),
        actor_id="conflict-user",
    )

    assert result.company is None
    assert result.partial is True
    assert "conflict" in result.warnings[0]
