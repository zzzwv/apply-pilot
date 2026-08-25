from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.company_intelligence.normalization import normalize_company_name
from app.company_intelligence.url_safety import normalize_url
from app.models.enums import LinkStatus, VerificationStatus


class CandidateSource(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    title: str = Field(min_length=1, max_length=512)
    source_type: str = Field(min_length=1, max_length=64)
    provider: str | None = Field(default=None, max_length=64)
    retrieved_at: datetime

    model_config = ConfigDict(extra="forbid")

    @field_validator("url")
    @classmethod
    def normalize_source_url(cls, value: str) -> str:
        return normalize_url(value)


class RecruitmentLinkCandidate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    url: str = Field(min_length=1, max_length=2048)
    channel_type: str = Field(min_length=1, max_length=64)
    claimed_official: bool = False
    source_url: str | None = Field(default=None, max_length=2048)
    evidence: str | None = None
    confidence: float = Field(default=0, ge=0, le=1)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    valid_status: LinkStatus = LinkStatus.UNKNOWN
    http_status: int | None = Field(default=None, ge=100, le=599)
    final_url: str | None = Field(default=None, max_length=2048)

    model_config = ConfigDict(extra="forbid")

    @field_validator("url", "source_url", "final_url")
    @classmethod
    def normalize_link_urls(cls, value: str | None) -> str | None:
        return normalize_url(value) if value is not None else None


class CompanyCandidate(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    short_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    company_nature: str | None = Field(default=None, max_length=64)
    company_size: str | None = Field(default=None, max_length=64)
    official_website: str | None = Field(default=None, max_length=2048)
    description: str | None = None
    recruitment_links: list[RecruitmentLinkCandidate] = Field(default_factory=list)
    sources: list[CandidateSource] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    model_config = ConfigDict(extra="forbid")

    @field_validator("company_name", "short_name")
    @classmethod
    def normalize_company_fields(cls, value: str | None) -> str | None:
        return normalize_company_name(value) if value is not None else None

    @field_validator("official_website")
    @classmethod
    def normalize_official_website(cls, value: str | None) -> str | None:
        return normalize_url(value) if value is not None else None


class CompanyIntelligenceSearchRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    force_refresh: bool = False

    model_config = ConfigDict(extra="forbid")

    @field_validator("company_name")
    @classmethod
    def normalize_requested_company_name(cls, value: str) -> str:
        return normalize_company_name(value)


class CompanyIntelligenceSearchResult(BaseModel):
    company: CompanyCandidate | None = None
    recruitment_links: list[RecruitmentLinkCandidate] = Field(default_factory=list)
    sources: list[CandidateSource] = Field(default_factory=list)
    partial: bool = False
    warnings: list[str] = Field(default_factory=list)
    allow_manual_input: bool = True

    model_config = ConfigDict(extra="forbid")
