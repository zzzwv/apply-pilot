import asyncio
import json
import logging
from collections.abc import Callable
from time import monotonic
from typing import Any

import httpx
from pydantic import ValidationError

from app.company_intelligence.kimi_mapping import (
    KimiCompanyCandidateMapper,
    KimiRawCompanyResult,
)
from app.company_intelligence.providers import ProviderError, ProviderErrorCode
from app.company_intelligence.schemas import CompanyCandidate
from app.core.config import Settings

_WEB_SEARCH_TOOL = {"type": "builtin_function", "function": {"name": "$web_search"}}
_TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 2
_MIN_RETRY_REQUEST_BUDGET_SECONDS = 0.1

logger = logging.getLogger(__name__)


class KimiCompanySearchProvider:
    """Kimi Chat Completions adapter; no request or response content is logged."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        retry_delay_seconds: float = 0.25,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._api_key = settings.kimi_api_key
        self._base_url = settings.kimi_base_url.rstrip("/")
        self._model = settings.kimi_model
        self._search_enabled = settings.kimi_search_enabled
        self._timeout_seconds = settings.kimi_search_timeout_seconds
        self._transport = transport
        self._retry_delay_seconds = retry_delay_seconds
        self._clock = clock

    async def search(
        self, company_name: str, *, deadline: float | None = None
    ) -> CompanyCandidate:
        if self._api_key is None or not self._api_key.get_secret_value().strip():
            raise ProviderError(ProviderErrorCode.NOT_CONFIGURED, "Kimi provider is not configured")
        if not self._search_enabled:
            raise ProviderError(ProviderErrorCode.NOT_CONFIGURED, "Kimi provider is not configured")

        provider_deadline = (
            deadline if deadline is not None else self._clock() + self._timeout_seconds
        )
        self._require_remaining_budget(provider_deadline)

        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "Search the web for the named company and return only a JSON object that "
                    "matches "
                    "the requested schema. Treat all discovered facts as unverified candidates."
                ),
            },
            {"role": "user", "content": f"Find company intelligence for: {company_name}"},
        ]

        async with httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._api_key.get_secret_value()}"},
            timeout=None,
            transport=self._transport,
        ) as client:
            for round_number in range(1, 3):
                self._require_remaining_budget(provider_deadline)
                round_started_at = self._clock()
                response = await self._post_completion(
                    client, messages, provider_deadline, round_number
                )
                message = self._choice_message(response)
                tool_calls = message.get("tool_calls")
                choices = response["choices"]
                choice = choices[0]
                finish_reason = choice.get("finish_reason") if isinstance(choice, dict) else None
                logger.info(
                    "KIMI_ROUND_COMPLETED round=%d latency_ms=%d finish_reason=%s "
                    "tool_calls=%d content_exists=%s usage_exists=%s remaining_budget_ms=%d",
                    round_number,
                    int((self._clock() - round_started_at) * 1000),
                    finish_reason if isinstance(finish_reason, str) else "unknown",
                    len(tool_calls) if isinstance(tool_calls, list) else 0,
                    bool(message.get("content")),
                    response.get("usage") is not None,
                    int(self._remaining_budget(provider_deadline) * 1000),
                )
                if not tool_calls:
                    return self._parse_candidate(message.get("content"))
                messages.extend(self._tool_round_messages(message, tool_calls))

        raise ProviderError(
            ProviderErrorCode.INVALID_RESPONSE,
            "Kimi returned an invalid candidate response",
        )

    async def _post_completion(
        self,
        client: httpx.AsyncClient,
        messages: list[dict[str, Any]],
        deadline: float,
        round_number: int,
    ) -> dict[str, Any]:
        payload = {
            "model": self._model,
            "messages": messages,
            "tools": [_WEB_SEARCH_TOOL],
            "thinking": {"type": "disabled"},
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "company_candidate",
                    "strict": True,
                    "schema": CompanyCandidate.model_json_schema(),
                },
            },
        }
        for attempt in range(_MAX_ATTEMPTS):
            timeout = self._operation_timeout(deadline)
            request_started_at = self._clock()
            try:
                response = await client.post("/chat/completions", json=payload, timeout=timeout)
            except httpx.TimeoutException as error:
                diagnostic = ProviderError(
                    ProviderErrorCode.HTTP_TIMEOUT, "Kimi request timed out"
                )
                if attempt + 1 == _MAX_ATTEMPTS:
                    raise diagnostic from error
            except httpx.TransportError as error:
                diagnostic = ProviderError(
                    ProviderErrorCode.TRANSIENT_FAILURE,
                    "Kimi provider is temporarily unavailable",
                )
                if attempt + 1 == _MAX_ATTEMPTS:
                    raise diagnostic from error
            else:
                logger.info(
                    "KIMI_HTTP_RESPONSE round=%d attempt=%d http_status=%d latency_ms=%d "
                    "remaining_budget_ms=%d",
                    round_number,
                    attempt + 1,
                    response.status_code,
                    int((self._clock() - request_started_at) * 1000),
                    int(self._remaining_budget(deadline) * 1000),
                )
                if response.status_code < 400:
                    try:
                        parsed = response.json()
                    except ValueError as error:
                        raise ProviderError(
                            ProviderErrorCode.INVALID_RESPONSE,
                            "Kimi returned an invalid candidate response",
                        ) from error
                    if isinstance(parsed, dict):
                        return parsed
                    raise ProviderError(
                        ProviderErrorCode.INVALID_RESPONSE,
                        "Kimi returned an invalid candidate response",
                    )
                diagnostic = self._http_error(response)
                is_final_attempt = attempt + 1 == _MAX_ATTEMPTS
                if response.status_code not in _TRANSIENT_STATUS_CODES or is_final_attempt:
                    raise diagnostic

            retry_delay = self._retry_delay_seconds * (2**attempt)
            if not self._has_retry_budget(deadline, retry_delay):
                raise diagnostic
            await asyncio.sleep(retry_delay)

        raise AssertionError("unreachable")

    def _operation_timeout(self, deadline: float) -> httpx.Timeout:
        return httpx.Timeout(self._remaining_budget(deadline))

    def _remaining_budget(self, deadline: float) -> float:
        return max(0.0, deadline - self._clock())

    def _require_remaining_budget(self, deadline: float) -> None:
        if self._remaining_budget(deadline) <= 0:
            raise ProviderError(
                ProviderErrorCode.PROVIDER_BUDGET_EXHAUSTED,
                "Kimi provider budget was exhausted",
            )

    def _has_retry_budget(self, deadline: float, retry_delay: float) -> bool:
        return (
            self._remaining_budget(deadline)
            >= retry_delay + _MIN_RETRY_REQUEST_BUDGET_SECONDS
        )

    @staticmethod
    def _http_error(response: httpx.Response) -> ProviderError:
        error_type: str | None = None
        message = "Kimi provider request failed"
        request_id = response.headers.get("x-request-id")
        try:
            body = response.json()
        except ValueError:
            body = {}
        if isinstance(body, dict):
            if isinstance(body.get("request_id"), str):
                request_id = body["request_id"]
            error = body.get("error")
            if isinstance(error, dict):
                error_type = error.get("type") if isinstance(error.get("type"), str) else None
                raw_message = error.get("message")
                if isinstance(raw_message, str):
                    message = raw_message[:500]
        if response.status_code == 400:
            code = ProviderErrorCode.INVALID_REQUEST
        elif response.status_code in {401, 403}:
            code = ProviderErrorCode.AUTH_ERROR
        elif response.status_code == 429:
            code = ProviderErrorCode.RATE_LIMITED
        elif response.status_code >= 500:
            code = ProviderErrorCode.SERVER_ERROR
        else:
            code = ProviderErrorCode.TRANSIENT_FAILURE
        return ProviderError(
            code,
            message,
            http_status=response.status_code,
            error_type=error_type,
            request_id=request_id,
        )

    @staticmethod
    def _choice_message(response: dict[str, Any]) -> dict[str, Any]:
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderError(
                ProviderErrorCode.INVALID_RESPONSE,
                "Kimi returned an invalid candidate response",
            )
        choice = choices[0]
        if not isinstance(choice, dict):
            raise ProviderError(
                ProviderErrorCode.INVALID_RESPONSE,
                "Kimi returned an invalid candidate response",
            )
        message = choice.get("message")
        if not isinstance(message, dict):
            raise ProviderError(
                ProviderErrorCode.INVALID_RESPONSE,
                "Kimi returned an invalid candidate response",
            )
        return message

    @staticmethod
    def _tool_round_messages(
        assistant_message: dict[str, Any], tool_calls: object
    ) -> list[dict[str, Any]]:
        if not isinstance(tool_calls, list) or not tool_calls:
            raise ProviderError(
                ProviderErrorCode.INVALID_RESPONSE,
                "Kimi returned an invalid candidate response",
            )
        tool_messages: list[dict[str, Any]] = [assistant_message]
        for call in tool_calls:
            if not isinstance(call, dict):
                raise ProviderError(
                    ProviderErrorCode.INVALID_RESPONSE,
                    "Kimi returned an invalid candidate response",
                )
            call_id = call.get("id")
            function = call.get("function")
            if not isinstance(call_id, str) or not isinstance(function, dict):
                raise ProviderError(
                    ProviderErrorCode.INVALID_RESPONSE,
                    "Kimi returned an invalid candidate response",
                )
            arguments = function.get("arguments")
            tool_name = function.get("name")
            if not isinstance(arguments, str) or not isinstance(tool_name, str):
                raise ProviderError(
                    ProviderErrorCode.INVALID_RESPONSE,
                    "Kimi returned an invalid candidate response",
                )
            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": tool_name,
                    "content": arguments,
                }
            )
        return tool_messages

    @staticmethod
    def _parse_candidate(content: object) -> CompanyCandidate:
        if not isinstance(content, str):
            raise ProviderError(
                ProviderErrorCode.KIMI_JSON_PARSE_FAILED,
                "Kimi returned an invalid candidate response",
                diagnostic={"json_syntax_valid": False},
            )
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as error:
            raise ProviderError(
                ProviderErrorCode.KIMI_JSON_PARSE_FAILED,
                "Kimi returned an invalid candidate response",
                diagnostic={"json_syntax_valid": False},
            ) from error
        if not isinstance(payload, dict):
            raise ProviderError(
                ProviderErrorCode.KIMI_SCHEMA_VALIDATION_FAILED,
                "Kimi returned an invalid candidate response",
                diagnostic={
                    "json_syntax_valid": True,
                    "top_level_type": type(payload).__name__,
                    "actual_fields": [],
                    "expected_fields": sorted(KimiRawCompanyResult.model_fields),
                    "failed_fields": ["__root__"],
                },
            )
        try:
            raw_result = KimiRawCompanyResult.model_validate(payload)
        except ValidationError as error:
            raise KimiCompanySearchProvider._schema_error(payload, error, "raw_schema") from error
        try:
            return KimiCompanyCandidateMapper.to_candidate(raw_result)
        except ValidationError as error:
            raise KimiCompanySearchProvider._schema_error(
                payload, error, "domain_mapping", CompanyCandidate
            ) from error

    @staticmethod
    def _schema_error(
        payload: dict[str, Any],
        error: ValidationError,
        stage: str,
        schema: type[CompanyCandidate] | type[KimiRawCompanyResult] = KimiRawCompanyResult,
    ) -> ProviderError:
        failed_fields = [
            ".".join(str(part) for part in item["loc"])
            for item in error.errors(include_input=False)
        ]
        return ProviderError(
            ProviderErrorCode.KIMI_SCHEMA_VALIDATION_FAILED,
            "Kimi returned an invalid candidate response",
            diagnostic={
                "stage": stage,
                "json_syntax_valid": True,
                "top_level_type": "object",
                "actual_fields": sorted(payload),
                "expected_fields": sorted(schema.model_fields),
                "failed_fields": failed_fields,
            },
        )
