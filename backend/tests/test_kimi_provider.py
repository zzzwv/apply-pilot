import json
import logging
from dataclasses import dataclass
from hashlib import sha256

import httpx
import pytest


def make_settings(**overrides: object):
    from app.core.config import Settings

    values = {
        "jwt_secret_key": "test-only-jwt-secret-at-least-32-bytes",
        "kimi_api_key": "test-kimi-api-key",
    }
    values.update(overrides)
    return Settings(**values)


def completion(content: str) -> dict[str, object]:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1_724_590_000,
        "model": "kimi-k2.5",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
    }


def candidate_json(**overrides: object) -> str:
    candidate = {
        "company_name": "腾讯科技有限公司",
        "company_aliases": ["腾讯"],
        "industry": "互联网",
        "ownership_type": "民营企业",
        "website": "https://www.tencent.com",
        "data_sources": [
            {
                "url": "https://www.tencent.com/about",
                "title": "公司介绍",
                "source_type": "official_site",
                "provider": "kimi",
                "retrieved_at": "2026-08-25T12:30:00Z",
            }
        ],
    }
    candidate.update(overrides)
    return json.dumps(candidate)


# Redacted fixture following the final-content contract observed at Kimi's
# `stop` boundary. Values are safe fixture data; model response text is never
# persisted in tests.
REDACTED_KIMI_FINAL_CONTENT_SHAPE = json.dumps(
    {
        "company_name": "武汉光庭信息技术股份有限公司",
        "company_aliases": ["光庭信息"],
        "industry": "软件和信息技术服务业",
        "ownership_type": "民营企业",
        "website": "https://www.kotei.com.cn",
        "data_sources": [
            {
                "url": "https://www.kotei.com.cn/",
                "title": "武汉光庭信息技术股份有限公司",
                "source_type": "official_site",
                "provider": "kimi",
                "retrieved_at": "2026-08-26T00:00:00Z",
            }
        ],
    }
)


# Field names come from the safe diagnostic summary of the one real Kimi
# tool-loop response. Values are synthetic; no provider response text is kept.
REDACTED_KIMI_RAW_COMPANY_RESULT_SHAPE = json.dumps(
    {
        "company_name": "武汉光庭信息技术股份有限公司",
        "company_aliases": ["光庭信息"],
        "industry": "软件和信息技术服务业",
        "ownership_type": "民营企业",
        "website": "https://www.kotei.com.cn",
        "employees": "500-999人",
        "business_scope": "软件研发与技术服务",
        "data_sources": [
            {
                "url": "https://www.kotei.com.cn/",
                "title": "武汉光庭信息技术股份有限公司",
                "source_type": "official_site",
                "retrieved_at": "2026-08-26T00:00:00Z",
            }
        ],
        "legal_representative": "测试代表",
        "registered_capital": "测试资本",
        "headquarters_location": "武汉",
        "stock_code": "300000",
        "listing_market": "测试市场",
        "listing_date": "2020-01-01",
        "major_shareholders": [],
        "ultimate_beneficial_owner": "测试受益人",
        "senior_executives": [],
        "financial_highlights": [],
        "business_segments": [],
        "major_clients": [],
        "subsidiaries": [],
        "affiliated_companies": [],
        "qualifications": [],
        "recent_developments": [],
        "risk_factors": [],
        "data_date": "2026-08-26",
        "confidence_level": "candidate",
    }
)


@dataclass
class FakeClock:
    now: float = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def request_timeout(request: httpx.Request) -> float:
    timeout = request.extensions["timeout"]
    assert isinstance(timeout, dict)
    value = timeout["read"]
    assert isinstance(value, float)
    return value


async def capture_tool_round_payloads() -> list[dict[str, object]]:
    """Run the real provider loop against a mock transport and retain JSON payloads only."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_requests.append(request)
        if len(seen_requests) == 1:
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
                                        "id": "call_schema",
                                        "type": "function",
                                        "function": {
                                            "name": "$web_search",
                                            "arguments": '{"q":"腾讯科技有限公司"}',
                                        },
                                    }
                                ],
                            },
                        }
                    ]
                },
            )
        return httpx.Response(200, json=completion(candidate_json()))

    provider = KimiCompanySearchProvider(
        make_settings(), transport=httpx.MockTransport(handler), retry_delay_seconds=0
    )
    await provider.search("腾讯科技有限公司")
    return [json.loads(request.content) for request in seen_requests]


@pytest.mark.asyncio
async def test_search_returns_validated_candidate_after_builtin_web_search_exchange(caplog) -> None:
    """Protects the Kimi boundary from returning prose instead of a traced candidate."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_requests.append(request)
        if len(seen_requests) == 1:
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-tool-call",
                    "object": "chat.completion",
                    "created": 1_724_590_000,
                    "model": "kimi-k2.5",
                    "choices": [
                        {
                            "index": 0,
                            "finish_reason": "tool_calls",
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call_web_search",
                                        "type": "function",
                                        "function": {
                                            "name": "$web_search",
                                            "arguments": '{"q":"腾讯科技有限公司"}',
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                },
            )
        return httpx.Response(200, json=completion(candidate_json()))

    provider = KimiCompanySearchProvider(
        make_settings(), transport=httpx.MockTransport(handler), retry_delay_seconds=0
    )

    caplog.set_level(logging.INFO, logger="app.company_intelligence.kimi")
    candidate = await provider.search("腾讯科技有限公司")

    assert candidate.company_name == "腾讯科技有限公司"
    assert candidate.sources[0].url == "https://www.tencent.com/about"
    assert len(seen_requests) == 2
    first_payload = json.loads(seen_requests[0].content)
    assert first_payload["model"] == "kimi-k2.5"
    assert first_payload["tools"] == [
        {"type": "builtin_function", "function": {"name": "$web_search"}}
    ]
    assert first_payload["thinking"] == {"type": "disabled"}
    second_payload = json.loads(seen_requests[1].content)
    assert second_payload["messages"][-1] == {
        "role": "tool",
        "tool_call_id": "call_web_search",
        "name": "$web_search",
        "content": '{"q":"腾讯科技有限公司"}',
    }
    assert "KIMI_ROUND_COMPLETED round=1" in caplog.text
    assert "KIMI_ROUND_COMPLETED round=2" in caplog.text


@pytest.mark.asyncio
async def test_kimi_response_format_declared_on_every_tool_round() -> None:
    """Both tool-loop requests retain model, thinking, tools and structured-output settings."""
    payloads = await capture_tool_round_payloads()

    assert len(payloads) == 2
    for payload in payloads:
        assert payload["model"] == "kimi-k2.5"
        assert payload["thinking"] == {"type": "disabled"}
        assert payload["tools"] == [
            {"type": "builtin_function", "function": {"name": "$web_search"}}
        ]
        assert payload["response_format"]["type"] == "json_schema"


@pytest.mark.asyncio
async def test_kimi_json_schema_is_identical_across_tool_rounds() -> None:
    """The tool result cannot silently replace or remove the structured-output schema."""
    payloads = await capture_tool_round_payloads()

    schema_hashes = [
        sha256(
            json.dumps(
                payload["response_format"]["json_schema"]["schema"],
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        for payload in payloads
    ]

    assert len(set(schema_hashes)) == 1


def test_kimi_tool_message_contains_name() -> None:
    """Kimi builtin web-search tool results identify the called builtin function."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider

    assistant_message = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": "call_web_search",
                "type": "function",
                "function": {"name": "$web_search", "arguments": '{"q":"Acme"}'},
            }
        ],
    }

    messages = KimiCompanySearchProvider._tool_round_messages(
        assistant_message, assistant_message["tool_calls"]
    )

    assert messages[0] is assistant_message
    assert messages[1]["tool_call_id"] == "call_web_search"
    assert messages[1]["name"] == "$web_search"


@pytest.mark.asyncio
async def test_search_reports_missing_configuration_without_an_http_request() -> None:
    """Protects deployments without a key from sending unauthenticated Kimi traffic."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider
    from app.company_intelligence.providers import ProviderError, ProviderErrorCode

    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail(f"unexpected request to {request.url}")

    provider = KimiCompanySearchProvider(
        make_settings(kimi_api_key=None), transport=httpx.MockTransport(handler)
    )

    with pytest.raises(ProviderError) as raised:
        await provider.search("腾讯科技有限公司")

    assert raised.value.code is ProviderErrorCode.NOT_CONFIGURED


@pytest.mark.asyncio
async def test_search_retries_one_rate_limited_response_before_returning_candidate() -> None:
    """Protects a recoverable Kimi rate limit from becoming an unnecessary manual fallback."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider

    attempt_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            return httpx.Response(429, json={"error": {"message": "busy"}})
        return httpx.Response(200, json=completion(candidate_json()))

    provider = KimiCompanySearchProvider(
        make_settings(), transport=httpx.MockTransport(handler), retry_delay_seconds=0
    )

    candidate = await provider.search("腾讯科技有限公司")

    assert candidate.industry == "互联网"
    assert attempt_count == 2


@pytest.mark.asyncio
async def test_kimi_http_400_keeps_sanitized_error() -> None:
    """Keeps actionable Kimi diagnostics without leaking credentials or raw headers."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider
    from app.company_intelligence.providers import ProviderError, ProviderErrorCode

    provider = KimiCompanySearchProvider(
        make_settings(),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                400,
                json={
                    "error": {
                        "type": "invalid_request_error",
                        "message": "response_format is incompatible with this request",
                    },
                    "request_id": "req_test_123",
                },
            )
        ),
    )

    with pytest.raises(ProviderError) as raised:
        await provider.search("腾讯科技有限公司")

    assert raised.value.code is ProviderErrorCode.INVALID_REQUEST
    assert raised.value.http_status == 400
    assert raised.value.error_type == "invalid_request_error"
    assert raised.value.request_id == "req_test_123"
    assert "response_format" in raised.value.sanitized_message
    assert "test-kimi-api-key" not in raised.value.sanitized_message


@pytest.mark.asyncio
async def test_search_reports_timeout_after_one_retry() -> None:
    """Protects callers from leaking HTTPX timeout details when Kimi is unavailable."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider
    from app.company_intelligence.providers import ProviderError, ProviderErrorCode

    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("timed out", request=request)

    provider = KimiCompanySearchProvider(
        make_settings(kimi_search_timeout_seconds=3),
        transport=httpx.MockTransport(handler),
        retry_delay_seconds=0,
    )

    with pytest.raises(ProviderError) as raised:
        await provider.search("腾讯科技有限公司")

    assert raised.value.code is ProviderErrorCode.TIMEOUT
    assert str(raised.value) == "Kimi request timed out"
    assert attempts == 2


@pytest.mark.asyncio
async def test_kimi_provider_uses_shared_deadline() -> None:
    """Every tool round must consume the single provider deadline."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider

    clock = FakeClock()
    observed_timeouts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        observed_timeouts.append(request_timeout(request))
        clock.advance(0.4)
        if len(observed_timeouts) == 1:
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "tool_calls": [
                                    {
                                        "id": "call_deadline",
                                        "type": "function",
                                        "function": {
                                            "name": "$web_search",
                                            "arguments": "{}",
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                },
            )
        return httpx.Response(200, json=completion(candidate_json()))

    provider = KimiCompanySearchProvider(
        make_settings(),
        transport=httpx.MockTransport(handler),
        retry_delay_seconds=0,
        clock=clock,
    )

    await provider.search("腾讯科技有限公司", deadline=1.0)

    assert observed_timeouts == [1.0, pytest.approx(0.6)]


@pytest.mark.asyncio
async def test_kimi_retry_does_not_reset_timeout_budget() -> None:
    """A fast transient response must leave the retry only the remaining time."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider

    clock = FakeClock()
    observed_timeouts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        observed_timeouts.append(request_timeout(request))
        clock.advance(0.4)
        if len(observed_timeouts) == 1:
            return httpx.Response(503, json={"error": {"message": "busy"}})
        return httpx.Response(200, json=completion(candidate_json()))

    provider = KimiCompanySearchProvider(
        make_settings(),
        transport=httpx.MockTransport(handler),
        retry_delay_seconds=0,
        clock=clock,
    )

    await provider.search("腾讯科技有限公司", deadline=1.0)

    assert observed_timeouts == [1.0, pytest.approx(0.6)]


@pytest.mark.asyncio
async def test_kimi_retry_skipped_when_budget_insufficient() -> None:
    """A near-expired deadline must not start a retry that cannot be useful."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider
    from app.company_intelligence.providers import ProviderError, ProviderErrorCode

    clock = FakeClock()
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        clock.advance(0.95)
        return httpx.Response(503, json={"error": {"message": "busy"}})

    provider = KimiCompanySearchProvider(
        make_settings(),
        transport=httpx.MockTransport(handler),
        retry_delay_seconds=0.1,
        clock=clock,
    )

    with pytest.raises(ProviderError) as raised:
        await provider.search("腾讯科技有限公司", deadline=1.0)

    assert raised.value.code is ProviderErrorCode.SERVER_ERROR
    assert attempts == 1


@pytest.mark.asyncio
async def test_provider_budget_exhaustion_is_classified() -> None:
    """An expired provider deadline is distinct from an HTTP operation timeout."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider
    from app.company_intelligence.providers import ProviderError, ProviderErrorCode

    clock = FakeClock(now=1.0)
    provider = KimiCompanySearchProvider(
        make_settings(),
        transport=httpx.MockTransport(lambda request: pytest.fail("unexpected HTTP request")),
        clock=clock,
    )

    with pytest.raises(ProviderError) as raised:
        await provider.search("腾讯科技有限公司", deadline=1.0)

    assert raised.value.code is ProviderErrorCode.PROVIDER_BUDGET_EXHAUSTED


@pytest.mark.asyncio
async def test_kimi_tool_round_uses_remaining_budget() -> None:
    """A tool exchange cannot reset the deadline granted before the first round."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider

    clock = FakeClock()
    observed_timeouts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        observed_timeouts.append(request_timeout(request))
        if len(observed_timeouts) == 1:
            clock.advance(0.7)
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "tool_calls": [
                                    {
                                        "id": "call_budget",
                                        "type": "function",
                                        "function": {
                                            "name": "$web_search",
                                            "arguments": "{}",
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                },
            )
        return httpx.Response(200, json=completion(candidate_json()))

    provider = KimiCompanySearchProvider(
        make_settings(),
        transport=httpx.MockTransport(handler),
        retry_delay_seconds=0,
        clock=clock,
    )

    await provider.search("腾讯科技有限公司", deadline=1.0)

    assert observed_timeouts[1] == pytest.approx(0.3)


@pytest.mark.asyncio
async def test_search_reports_invalid_json_without_exposing_response_content() -> None:
    """Protects callers from trusting malformed model output or receiving its raw text."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider
    from app.company_intelligence.providers import ProviderError, ProviderErrorCode

    provider = KimiCompanySearchProvider(
        make_settings(),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=completion("not-json"))
        ),
    )

    with pytest.raises(ProviderError) as raised:
        await provider.search("腾讯科技有限公司")

    assert raised.value.code is ProviderErrorCode.KIMI_JSON_PARSE_FAILED
    assert str(raised.value) == "Kimi returned an invalid candidate response"


@pytest.mark.asyncio
async def test_search_accepts_partial_json_candidate_with_safe_schema_defaults() -> None:
    """Protects usable minimal structured results from being discarded as all-or-nothing."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider

    provider = KimiCompanySearchProvider(
        make_settings(),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json=completion(json.dumps({"company_name": "腾讯科技有限公司"})),
            )
        ),
    )

    candidate = await provider.search("腾讯科技有限公司")

    assert candidate.company_name == "腾讯科技有限公司"
    assert candidate.recruitment_links == []
    assert candidate.sources == []


def test_kimi_real_shape_fixture_extraction() -> None:
    """A redacted Kimi final-content shape still traverses strict candidate validation."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider

    candidate = KimiCompanySearchProvider._parse_candidate(
        REDACTED_KIMI_FINAL_CONTENT_SHAPE
    )

    assert candidate.company_name == "武汉光庭信息技术股份有限公司"
    assert len(candidate.sources) == 1
    assert candidate.sources[0].source_type == "official_site"


def test_kimi_raw_company_result_is_mapped_to_the_strict_domain_candidate() -> None:
    """Provider field names are translated at the boundary, not added to the domain model."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider

    candidate = KimiCompanySearchProvider._parse_candidate(
        REDACTED_KIMI_RAW_COMPANY_RESULT_SHAPE
    )

    assert candidate.company_name == "武汉光庭信息技术股份有限公司"
    assert candidate.short_name == "光庭信息"
    assert candidate.company_nature == "民营企业"
    assert candidate.company_size == "500-999人"
    assert candidate.official_website == "https://www.kotei.com.cn"
    assert candidate.sources[0].url == "https://www.kotei.com.cn/"
    assert "website" not in candidate.model_fields_set
    assert "ownership_type" not in candidate.model_fields_set
    assert "data_sources" not in candidate.model_fields_set


def test_kimi_json_parse_error_classification() -> None:
    """Malformed final content is diagnosed separately from an otherwise valid schema failure."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider
    from app.company_intelligence.providers import ProviderError, ProviderErrorCode

    with pytest.raises(ProviderError) as raised:
        KimiCompanySearchProvider._parse_candidate('{"company_name":')

    assert raised.value.code is ProviderErrorCode.KIMI_JSON_PARSE_FAILED
    assert raised.value.diagnostic == {"json_syntax_valid": False}


def test_kimi_schema_validation_error_classification() -> None:
    """Valid JSON with invalid candidate fields keeps a safe field-level diagnostic summary."""
    from app.company_intelligence.kimi import KimiCompanySearchProvider
    from app.company_intelligence.providers import ProviderError, ProviderErrorCode

    invalid_schema = json.dumps(
        {
            "company_name": "武汉光庭信息技术股份有限公司",
            "data_sources": [
                {
                    "url": "https://www.kotei.com.cn/",
                    "title": "官网",
                    "source_type": "official_site",
                    "retrieved_at": "not-a-datetime",
                }
            ],
        }
    )

    with pytest.raises(ProviderError) as raised:
        KimiCompanySearchProvider._parse_candidate(invalid_schema)

    assert raised.value.code is ProviderErrorCode.KIMI_SCHEMA_VALIDATION_FAILED
    assert raised.value.diagnostic["json_syntax_valid"] is True
    assert raised.value.diagnostic["top_level_type"] == "object"
    assert "company_name" in raised.value.diagnostic["actual_fields"]
    assert raised.value.diagnostic["stage"] == "raw_schema"
    assert "data_sources.0.retrieved_at" in raised.value.diagnostic["failed_fields"]
