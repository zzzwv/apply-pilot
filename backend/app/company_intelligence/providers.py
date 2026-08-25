from enum import StrEnum
from typing import Protocol

from app.company_intelligence.schemas import CompanyCandidate


class ProviderErrorCode(StrEnum):
    NOT_CONFIGURED = "not_configured"
    TIMEOUT = "timeout"
    TRANSIENT_FAILURE = "transient_failure"
    INVALID_RESPONSE = "invalid_response"


class ProviderError(Exception):
    """A safe, provider-independent error suitable for an intelligence fallback."""

    def __init__(self, code: ProviderErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class CompanySearchProvider(Protocol):
    async def search(self, company_name: str) -> CompanyCandidate:
        """Return an unpersisted company candidate for a name."""
