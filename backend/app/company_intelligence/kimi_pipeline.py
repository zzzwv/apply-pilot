"""Strict two-stage contracts for Kimi search evidence and canonical extraction."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CompanyNature = Literal[
    "STATE_OWNED",
    "CENTRAL_OWNED",
    "PRIVATE",
    "FOREIGN",
    "JOINT_VENTURE",
    "STARTUP",
]
CompanySize = Literal["50以下", "50-200", "200-500", "500-1000", "1000-5000", "5000以上"]
RecruitmentChannel = Literal[
    "official_campus",
    "official_internship",
    "official_social",
    "official_wechat",
    "boss",
    "zhilian",
    "51job",
    "nowcoder",
    "shixiseng",
    "school",
    "other",
]


class SearchEvidenceSource(BaseModel):
    """A stable Stage A source/URL registry entry, never model-generated in Stage B."""

    source_id: str = Field(pattern=r"^S[1-9][0-9]*$")
    url_id: str = Field(pattern=r"^U[1-9][0-9]*$")
    title: str = Field(min_length=1, max_length=512)
    url: str = Field(min_length=1, max_length=2048)
    source_type: str = Field(min_length=1, max_length=64)
    snippet: str | None = None

    model_config = ConfigDict(extra="forbid")


class KimiSearchEvidence(BaseModel):
    """Untrusted, non-persisted output of the web-search stage."""

    final_content: str = Field(min_length=1)
    sources: list[SearchEvidenceSource] = Field(default_factory=list)
    tool_round_count: int = Field(ge=0)
    provider: Literal["kimi"]
    model: str = Field(min_length=1, max_length=128)
    retrieved_at: datetime

    model_config = ConfigDict(extra="forbid")


class KimiCanonicalRecruitmentReference(BaseModel):
    """Stage B classification of a Stage A URL; it cannot carry a raw URL."""

    url_id: str = Field(pattern=r"^U[1-9][0-9]*$")
    channel_type: RecruitmentChannel
    claimed_official: bool = False
    evidence: str | None = None

    model_config = ConfigDict(extra="forbid")


class KimiCanonicalExtractionResult(BaseModel):
    """Strict provider extraction contract, deliberately separate from the domain candidate."""

    full_name: str = Field(min_length=1, max_length=255)
    short_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    company_nature_raw: str | None = Field(default=None, max_length=128)
    company_size_raw: str | int | float | None = None
    official_website_url_id: str | None = Field(default=None, pattern=r"^U[1-9][0-9]*$")
    description: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    recruitment_links: list[KimiCanonicalRecruitmentReference] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
