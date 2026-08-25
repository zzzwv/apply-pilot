import json

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
        "industry": "互联网",
        "sources": [
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


@pytest.mark.asyncio
async def test_search_returns_validated_candidate_after_builtin_web_search_exchange() -> None:
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
        "content": '{"q":"腾讯科技有限公司"}',
    }


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

    assert raised.value.code is ProviderErrorCode.INVALID_RESPONSE
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
