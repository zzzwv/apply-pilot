from enum import StrEnum
from typing import Any, Protocol

from app.company_intelligence.schemas import CompanyCandidate


class ProviderErrorCode(StrEnum):
    NOT_CONFIGURED = "not_configured"
    INVALID_REQUEST = "kimi_invalid_request"
    AUTH_ERROR = "kimi_auth_error"
    RATE_LIMITED = "kimi_rate_limited"
    SERVER_ERROR = "kimi_server_error"
    HTTP_TIMEOUT = "kimi_http_timeout"
    # Backward-compatible alias for internal callers that used the original name.
    TIMEOUT = HTTP_TIMEOUT
    PROVIDER_CANCELLED_BY_SERVICE_TIMEOUT = "kimi_provider_cancelled_by_service_timeout"
    PROVIDER_BUDGET_EXHAUSTED = "kimi_provider_budget_exhausted"
    KIMI_JSON_PARSE_FAILED = "KIMI_JSON_PARSE_FAILED"
    KIMI_SCHEMA_VALIDATION_FAILED = "KIMI_SCHEMA_VALIDATION_FAILED"
    KIMI_SEARCH_HTTP_ERROR = "kimi_search_http_error"
    KIMI_SEARCH_TIMEOUT = "kimi_search_timeout"
    KIMI_SEARCH_BUDGET_EXHAUSTED = "kimi_search_budget_exhausted"
    KIMI_EXTRACTION_HTTP_ERROR = "kimi_extraction_http_error"
    KIMI_EXTRACTION_JSON_PARSE_FAILED = "kimi_extraction_json_parse_failed"
    KIMI_EXTRACTION_SCHEMA_VALIDATION_FAILED = "kimi_extraction_schema_validation_failed"
    KIMI_EXTRACTION_BUDGET_EXHAUSTED = "kimi_extraction_budget_exhausted"
    KIMI_SOURCE_REFERENCE_INVALID = "kimi_source_reference_invalid"
    KIMI_URL_REFERENCE_INVALID = "kimi_url_reference_invalid"
    KIMI_CANONICAL_MAPPING_FAILED = "kimi_canonical_mapping_failed"
    TRANSIENT_FAILURE = "transient_failure"
    INVALID_RESPONSE = "invalid_response"


class ProviderError(Exception):
    """A safe, provider-independent error suitable for an intelligence fallback."""

    def __init__(
        self,
        code: ProviderErrorCode,
        message: str,
        *,
        http_status: int | None = None,
        error_type: str | None = None,
        request_id: str | None = None,
        diagnostic: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.error_type = error_type
        self.request_id = request_id
        self.sanitized_message = message
        self.diagnostic = diagnostic or {}


class CompanySearchProvider(Protocol):
    async def search(
        self, company_name: str, *, deadline: float | None = None
    ) -> CompanyCandidate:
        """Return an unpersisted company candidate for a name."""
