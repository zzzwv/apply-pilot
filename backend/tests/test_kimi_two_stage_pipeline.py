import json
import logging
from datetime import UTC, datetime
from time import monotonic

import httpx
import pytest
from pydantic import ValidationError


def evidence() -> object:
    from app.company_intelligence.kimi_pipeline import KimiSearchEvidence, SearchEvidenceSource

    sources = [
        SearchEvidenceSource(
            source_id=f"S{index}",
            url_id=f"U{index}",
            title=f"Acme evidence source {index}",
            url=f"https://evidence{index}.acme.example/company",
            source_type="web_search",
            snippet=f"Sanitized public evidence {index}",
        )
        for index in range(1, 13)
    ]
    return KimiSearchEvidence(
        final_content="sanitized untrusted public search evidence",
        sources=sources,
        tool_round_count=2,
        provider="kimi",
        model="kimi-k2.5",
        retrieved_at=datetime(2026, 8, 26, tzinfo=UTC),
    )


def extraction_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "full_name": "Acme Corporation",
        "short_name": "Acme",
        "industry": "Software",
        "company_nature_raw": "private enterprise",
        "company_size_raw": "about 300 employees",
        "official_website_url_id": "U1",
        "description": "Public software company profile.",
        "source_ids": ["S1", "S2"],
        "recruitment_links": [
            {
                "url_id": "U2",
                "channel_type": "official_campus",
                "claimed_official": True,
            }
        ],
    }
    payload.update(overrides)
    return payload


def extraction_result(**overrides: object) -> object:
    from app.company_intelligence.kimi_pipeline import KimiCanonicalExtractionResult

    return KimiCanonicalExtractionResult.model_validate(extraction_payload(**overrides))


def test_stage_b_uses_source_ids_not_source_objects() -> None:
    result = extraction_result()

    assert result.source_ids == ["S1", "S2"]
    assert "sources" not in result.model_dump()
    with pytest.raises(ValidationError):
        extraction_result(sources=[{"url": "https://invented.example"}])


def test_source_id_resolves_to_stage_a_source() -> None:
    from app.company_intelligence.kimi_mapping import KimiCompanyCandidateMapper

    candidate = KimiCompanyCandidateMapper.to_candidate(extraction_result(), evidence())

    assert [source.url for source in candidate.sources] == [
        "https://evidence1.acme.example/company",
        "https://evidence2.acme.example/company",
    ]


def test_unknown_source_id_is_rejected() -> None:
    from app.company_intelligence.kimi_mapping import (
        KimiCompanyCandidateMapper,
        UnknownSourceReferenceError,
    )

    with pytest.raises(UnknownSourceReferenceError):
        KimiCompanyCandidateMapper.to_candidate(
            extraction_result(source_ids=["S999"]), evidence()
        )


def test_stage_b_cannot_invent_source_url() -> None:
    with pytest.raises(ValidationError):
        extraction_result(
            source_ids=["S1"],
            sources=[
                {
                    "title": "invented",
                    "url": "https://invented.example/source",
                    "source_type": "web_search",
                }
            ],
        )


def test_recruitment_url_ref_resolves_from_stage_a() -> None:
    from app.company_intelligence.kimi_mapping import KimiCompanyCandidateMapper

    candidate = KimiCompanyCandidateMapper.to_candidate(extraction_result(), evidence())

    assert candidate.recruitment_links[0].url == "https://evidence2.acme.example/company"
    assert candidate.recruitment_links[0].channel_type == "official_campus"


def test_unknown_recruitment_url_ref_is_rejected() -> None:
    from app.company_intelligence.kimi_mapping import (
        KimiCompanyCandidateMapper,
        UnknownUrlReferenceError,
    )

    with pytest.raises(UnknownUrlReferenceError):
        KimiCompanyCandidateMapper.to_candidate(
            extraction_result(
                recruitment_links=[
                    {"url_id": "U999", "channel_type": "official_campus"}
                ]
            ),
            evidence(),
        )


def test_company_nature_chinese_alias_normalized() -> None:
    from app.company_intelligence.kimi_mapping import normalize_company_nature

    assert normalize_company_nature("国有企业") == "STATE_OWNED"


def test_company_nature_english_alias_normalized() -> None:
    from app.company_intelligence.kimi_mapping import normalize_company_nature

    assert normalize_company_nature("private enterprise") == "PRIVATE"


def test_unknown_company_nature_becomes_null() -> None:
    from app.company_intelligence.kimi_mapping import KimiCompanyCandidateMapper

    candidate = KimiCompanyCandidateMapper.to_candidate(
        extraction_result(company_nature_raw="diversified technology company"), evidence()
    )

    assert candidate.company_nature is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("about 300 employees", "200-500"), ("约 1200 人", "1000-5000"), ("10000+", "5000以上")],
)
def test_company_size_normalization(raw: str, expected: str) -> None:
    from app.company_intelligence.kimi_mapping import normalize_company_size

    assert normalize_company_size(raw) == expected


def test_canonical_extraction_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        extraction_result(founding_date="2020-01-01")


def test_search_evidence_is_not_company_candidate() -> None:
    from app.company_intelligence.kimi_pipeline import KimiSearchEvidence
    from app.company_intelligence.schemas import CompanyCandidate

    value = evidence()
    assert isinstance(value, KimiSearchEvidence)
    assert not isinstance(value, CompanyCandidate)


def test_search_evidence_preserves_stable_source_registry_ids() -> None:
    result = evidence()

    assert len(result.sources) == 12
    assert result.sources[0].source_id == "S1"
    assert result.sources[-1].url_id == "U12"


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class StaticWebSearch:
    def __init__(self, result: object, clock: FakeClock | None = None, duration: float = 0) -> None:
        self.result = result
        self.clock = clock
        self.duration = duration
        self.deadlines: list[float] = []

    async def search(self, company_name: str, *, deadline: float) -> object:
        del company_name
        self.deadlines.append(deadline)
        if self.clock is not None:
            self.clock.advance(self.duration)
        return self.result


class StaticExtractor:
    def __init__(self, result: object) -> None:
        self.result = result
        self.deadlines: list[float] = []

    async def extract(self, search_evidence: object, *, deadline: float) -> object:
        del search_evidence
        self.deadlines.append(deadline)
        return self.result


@pytest.mark.asyncio
async def test_two_stage_pipeline_builds_strict_company_candidate() -> None:
    from app.company_intelligence.kimi_two_stage import KimiTwoStageCompanyProvider
    from app.core.config import Settings

    stage_a = StaticWebSearch(evidence())
    stage_b = StaticExtractor(extraction_result())
    provider = KimiTwoStageCompanyProvider(
        Settings(jwt_secret_key="test-only-jwt-secret-at-least-32-bytes"),
        web_search=stage_a,
        extractor=stage_b,
    )

    candidate = await provider.search("Acme", deadline=monotonic() + 10)

    assert candidate.company_name == "acme corporation"
    assert candidate.company_nature == "PRIVATE"
    assert candidate.company_size == "200-500"
    assert candidate.official_website == "https://evidence1.acme.example/company"
    assert candidate.sources[0].title == "Acme evidence source 1"
    assert stage_a.deadlines == stage_b.deadlines


@pytest.mark.asyncio
async def test_extraction_uses_remaining_search_budget() -> None:
    from app.company_intelligence.kimi_two_stage import KimiTwoStageCompanyProvider
    from app.core.config import Settings

    clock = FakeClock()
    stage_a = StaticWebSearch(evidence(), clock=clock, duration=0.7)
    stage_b = StaticExtractor(extraction_result())
    provider = KimiTwoStageCompanyProvider(
        Settings(jwt_secret_key="test-only-jwt-secret-at-least-32-bytes"),
        web_search=stage_a,
        extractor=stage_b,
        clock=clock,
    )

    await provider.search("Acme", deadline=1.0)

    assert stage_a.deadlines == [1.0]
    assert stage_b.deadlines == [1.0]
    assert stage_b.deadlines[0] - clock() == pytest.approx(0.3)


@pytest.mark.asyncio
async def test_extraction_does_not_reset_deadline() -> None:
    from app.company_intelligence.kimi_two_stage import KimiTwoStageCompanyProvider
    from app.core.config import Settings

    clock = FakeClock()
    stage_a = StaticWebSearch(evidence(), clock=clock, duration=0.5)
    stage_b = StaticExtractor(extraction_result())
    provider = KimiTwoStageCompanyProvider(
        Settings(jwt_secret_key="test-only-jwt-secret-at-least-32-bytes"),
        web_search=stage_a,
        extractor=stage_b,
        clock=clock,
    )

    await provider.search("Acme", deadline=1.0)

    assert stage_a.deadlines[0] == stage_b.deadlines[0] == 1.0


@pytest.mark.asyncio
async def test_extraction_skipped_when_budget_exhausted() -> None:
    from app.company_intelligence.kimi_two_stage import KimiTwoStageCompanyProvider
    from app.company_intelligence.providers import ProviderError, ProviderErrorCode
    from app.core.config import Settings

    clock = FakeClock()
    stage_a = StaticWebSearch(evidence(), clock=clock, duration=1.0)
    stage_b = StaticExtractor(extraction_result())
    provider = KimiTwoStageCompanyProvider(
        Settings(jwt_secret_key="test-only-jwt-secret-at-least-32-bytes"),
        web_search=stage_a,
        extractor=stage_b,
        clock=clock,
    )

    with pytest.raises(ProviderError) as raised:
        await provider.search("Acme", deadline=1.0)

    assert raised.value.code is ProviderErrorCode.KIMI_EXTRACTION_BUDGET_EXHAUSTED
    assert stage_b.deadlines == []


@pytest.mark.asyncio
async def test_web_search_returns_search_evidence(caplog: pytest.LogCaptureFixture) -> None:
    from app.company_intelligence.kimi_two_stage import KimiWebSearchProvider
    from app.core.config import Settings

    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "finish_reason": "tool_calls",
                            "message": {
                                "role": "assistant",
                                "tool_calls": [
                                    {
                                        "id": "call_search",
                                        "type": "function",
                                        "function": {
                                            "name": "$web_search",
                                            "arguments": '{"q":"Acme"}',
                                        },
                                    }
                                ],
                            },
                        }
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": "Official page https://www.acme.example/about",
                        },
                    }
                ]
            },
        )

    provider = KimiWebSearchProvider(
        Settings(
            jwt_secret_key="test-only-jwt-secret-at-least-32-bytes",
            kimi_api_key="test-kimi-api-key",
        ),
        transport=httpx.MockTransport(handler),
        retry_delay_seconds=0,
    )

    with caplog.at_level(logging.INFO, logger="app.company_intelligence.kimi_two_stage"):
        result = await provider.search("Acme", deadline=monotonic() + 10)

    payloads = [json.loads(request.content) for request in requests]
    assert result.tool_round_count == 2
    assert result.sources[0].source_id == "S1"
    assert result.sources[0].url_id == "U1"
    assert all("response_format" not in payload for payload in payloads)
    assert all(payload["tools"][0]["function"]["name"] == "$web_search" for payload in payloads)
    assert "recruitment" in payloads[0]["messages"][0]["content"].casefold()
    assert "recruitment" in payloads[0]["messages"][1]["content"].casefold()
    assert payloads[1]["messages"][-2]["role"] == "assistant"
    assert payloads[1]["messages"][-1] == {
        "role": "tool",
        "tool_call_id": "call_search",
        "name": "$web_search",
        "content": '{"q":"Acme"}',
    }
    assert sum("KIMI_SEARCH_ROUND" in record.message for record in caplog.records) == 2


@pytest.mark.asyncio
async def test_canonical_extraction_valid(caplog: pytest.LogCaptureFixture) -> None:
    from app.company_intelligence.kimi_two_stage import KimiCanonicalExtractor
    from app.core.config import Settings

    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(extraction_payload()),
                        },
                    }
                ]
            },
        )

    extractor = KimiCanonicalExtractor(
        Settings(
            jwt_secret_key="test-only-jwt-secret-at-least-32-bytes",
            kimi_api_key="test-kimi-api-key",
        ),
        transport=httpx.MockTransport(handler),
        retry_delay_seconds=0,
    )

    with caplog.at_level(logging.INFO, logger="app.company_intelligence.kimi_two_stage"):
        result = await extractor.extract(evidence(), deadline=monotonic() + 10)

    payload = json.loads(requests[0].content)
    assert result.full_name == "Acme Corporation"
    assert result.source_ids == ["S1", "S2"]
    assert payload["response_format"]["type"] == "json_schema"
    assert "tools" not in payload
    assert any("KIMI_EXTRACTION_COMPLETED" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_canonical_extraction_normalizes_observed_legacy_recruitment_fields() -> None:
    """Keep evidence-backed links when Kimi uses its legacy per-link field names."""

    from app.company_intelligence.kimi_two_stage import KimiCanonicalExtractor
    from app.core.config import Settings

    legacy_payload = extraction_payload(
        recruitment_links=[
            {"url_id": "U2", "type": "official_campus", "source_ids": ["S2"]},
            {
                "url_id": "U3",
                "link_type": "official",
                "source_ids": ["S3"],
                "url": "https://model-invented.example/jobs",
            },
        ]
    )
    legacy_payload.pop("industry")

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": json.dumps(legacy_payload)},
                    }
                ]
            },
        )

    extractor = KimiCanonicalExtractor(
        Settings(
            jwt_secret_key="test-only-jwt-secret-at-least-32-bytes",
            kimi_api_key="test-kimi-api-key",
        ),
        transport=httpx.MockTransport(handler),
        retry_delay_seconds=0,
    )

    result = await extractor.extract(evidence(), deadline=monotonic() + 10)

    assert result.industry is None
    links = [
        (link.url_id, link.channel_type, link.claimed_official)
        for link in result.recruitment_links
    ]
    assert links == [
        ("U2", "official_campus", False),
        ("U3", "other", True),
    ]


@pytest.mark.asyncio
async def test_canonical_extraction_keeps_only_evidence_backed_legacy_links_from_fenced_json(
) -> None:
    """Kimi's non-canonical links must resolve through Stage A, never its raw URL text."""

    from app.company_intelligence.kimi_two_stage import KimiCanonicalExtractor
    from app.core.config import Settings

    legacy_payload = extraction_payload(
        recruitment_links=[
            {"type": "official_campus", "source_ids": ["S2"]},
            {
                "link_type": "official",
                "url": "https://evidence3.acme.example/company",
            },
            {"url": "https://model-invented.example/jobs", "type": "official_social"},
        ]
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": f"```json\n{json.dumps(legacy_payload)}\n```",
                        },
                    }
                ]
            },
        )

    extractor = KimiCanonicalExtractor(
        Settings(
            jwt_secret_key="test-only-jwt-secret-at-least-32-bytes",
            kimi_api_key="test-kimi-api-key",
        ),
        transport=httpx.MockTransport(handler),
        retry_delay_seconds=0,
    )

    result = await extractor.extract(evidence(), deadline=monotonic() + 10)

    links = [
        (link.url_id, link.channel_type, link.claimed_official)
        for link in result.recruitment_links
    ]
    assert links == [
        ("U2", "official_campus", False),
        ("U3", "other", True),
    ]


@pytest.mark.asyncio
async def test_kimi_json_parse_error_classification() -> None:
    from app.company_intelligence.kimi_two_stage import KimiCanonicalExtractor
    from app.company_intelligence.providers import ProviderError, ProviderErrorCode
    from app.core.config import Settings

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "{not-json"},
                    }
                ]
            },
        )

    extractor = KimiCanonicalExtractor(
        Settings(
            jwt_secret_key="test-only-jwt-secret-at-least-32-bytes",
            kimi_api_key="test-kimi-api-key",
        ),
        transport=httpx.MockTransport(handler),
        retry_delay_seconds=0,
    )

    with pytest.raises(ProviderError) as raised:
        await extractor.extract(evidence(), deadline=monotonic() + 10)

    assert raised.value.code is ProviderErrorCode.KIMI_EXTRACTION_JSON_PARSE_FAILED
