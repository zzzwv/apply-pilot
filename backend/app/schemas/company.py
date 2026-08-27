from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.company_intelligence.normalization import normalize_company_name
from app.company_intelligence.schemas import CompanyCandidate, RecruitmentLinkCandidate


class CompanyCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    short_name: str | None = Field(default=None, max_length=255)
    nature: str | None = Field(default=None, max_length=64)
    size: str | None = Field(default=None, max_length=64)
    industry: str | None = Field(default=None, max_length=128)
    headquarters_city: str | None = Field(default=None, max_length=128)
    business_description: str | None = None
    founded_date: date | None = None
    registered_capital: str | None = Field(default=None, max_length=128)
    official_website: str | None = Field(default=None, max_length=2048)

    model_config = {"extra": "forbid"}


class CompanyRead(BaseModel):
    id: UUID
    full_name: str

    model_config = {"from_attributes": True}


class CompanyDetailRead(CompanyRead):
    short_name: str | None
    industry: str | None
    nature: str | None
    size: str | None
    official_website: str | None
    business_description: str | None


class CompanyUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    short_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    nature: str | None = Field(default=None, max_length=64)
    size: str | None = Field(default=None, max_length=64)
    official_website: str | None = Field(default=None, max_length=2048)
    business_description: str | None = None

    model_config = {"extra": "forbid"}


class CompanyIntelligenceConfirmRequest(BaseModel):
    """User-edited candidate data that may be persisted only after explicit confirmation."""

    company: CompanyCandidate
    aliases: list[str] = Field(default_factory=list, max_length=50)
    selected_recruitment_links: list[RecruitmentLinkCandidate] = Field(
        default_factory=list, max_length=50
    )

    model_config = {"extra": "forbid"}

    @classmethod
    def _normalize_alias(cls, value: str) -> str:
        normalized = normalize_company_name(value)
        if not normalized:
            raise ValueError("alias must not be empty")
        return normalized

    @classmethod
    def _validate_aliases(cls, values: list[str]) -> list[str]:
        return [cls._normalize_alias(value) for value in values]

    _normalize_aliases = field_validator("aliases")(_validate_aliases)


class ConfirmedRecruitmentLinkRead(BaseModel):
    url: str
    title: str
    channel_type: str
    claimed_official: bool


class CompanyIntelligenceConfirmResponse(BaseModel):
    company: CompanyRead
    created: bool
    aliases: list[str]
    recruitment_links: list[ConfirmedRecruitmentLinkRead]
