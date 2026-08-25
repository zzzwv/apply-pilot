import asyncio
from typing import Any

import httpx
from pydantic import ValidationError

from app.company_intelligence.providers import ProviderError, ProviderErrorCode
from app.company_intelligence.schemas import CompanyCandidate
from app.core.config import Settings

_WEB_SEARCH_TOOL = {"type": "builtin_function", "function": {"name": "$web_search"}}
_TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 2


class KimiCompanySearchProvider:
    """Kimi Chat Completions adapter; no request or response content is logged."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        retry_delay_seconds: float = 0.25,
    ) -> None:
        self._api_key = settings.kimi_api_key
        self._base_url = settings.kimi_base_url.rstrip("/")
        self._model = settings.kimi_model
        self._search_enabled = settings.kimi_search_enabled
        self._timeout_seconds = settings.kimi_search_timeout_seconds
        self._transport = transport
        self._retry_delay_seconds = retry_delay_seconds

    async def search(self, company_name: str) -> CompanyCandidate:
        if self._api_key is None or not self._api_key.get_secret_value().strip():
            raise ProviderError(ProviderErrorCode.NOT_CONFIGURED, "Kimi provider is not configured")
        if not self._search_enabled:
            raise ProviderError(ProviderErrorCode.NOT_CONFIGURED, "Kimi provider is not configured")

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
            timeout=httpx.Timeout(float(self._timeout_seconds)),
            transport=self._transport,
        ) as client:
            for _ in range(2):
                response = await self._post_completion(client, messages)
                message = self._choice_message(response)
                tool_calls = message.get("tool_calls")
                if not tool_calls:
                    return self._parse_candidate(message.get("content"))
                messages.extend(self._tool_round_messages(message, tool_calls))

        raise ProviderError(
            ProviderErrorCode.INVALID_RESPONSE,
            "Kimi returned an invalid candidate response",
        )

    async def _post_completion(
        self, client: httpx.AsyncClient, messages: list[dict[str, Any]]
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
            try:
                response = await client.post("/chat/completions", json=payload)
            except httpx.TimeoutException as error:
                if attempt + 1 == _MAX_ATTEMPTS:
                    raise ProviderError(
                        ProviderErrorCode.TIMEOUT, "Kimi request timed out"
                    ) from error
            except httpx.TransportError as error:
                if attempt + 1 == _MAX_ATTEMPTS:
                    raise ProviderError(
                        ProviderErrorCode.TRANSIENT_FAILURE,
                        "Kimi provider is temporarily unavailable",
                    ) from error
            else:
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
                is_final_attempt = attempt + 1 == _MAX_ATTEMPTS
                if response.status_code not in _TRANSIENT_STATUS_CODES or is_final_attempt:
                    raise ProviderError(
                        ProviderErrorCode.TRANSIENT_FAILURE,
                        "Kimi provider is temporarily unavailable",
                    )

            await asyncio.sleep(self._retry_delay_seconds * (2**attempt))

        raise AssertionError("unreachable")

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
            if not isinstance(arguments, str):
                raise ProviderError(
                    ProviderErrorCode.INVALID_RESPONSE,
                    "Kimi returned an invalid candidate response",
                )
            tool_messages.append(
                {"role": "tool", "tool_call_id": call_id, "content": arguments}
            )
        return tool_messages

    @staticmethod
    def _parse_candidate(content: object) -> CompanyCandidate:
        if not isinstance(content, str):
            raise ProviderError(
                ProviderErrorCode.INVALID_RESPONSE,
                "Kimi returned an invalid candidate response",
            )
        try:
            return CompanyCandidate.model_validate_json(content)
        except (ValidationError, ValueError) as error:
            raise ProviderError(
                ProviderErrorCode.INVALID_RESPONSE,
                "Kimi returned an invalid candidate response",
            ) from error
