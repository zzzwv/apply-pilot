"""Provider-only Kimi result contract and its explicit domain mapper."""

import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from app.company_intelligence.kimi_pipeline import (
    KimiCanonicalExtractionResult,
    KimiSearchEvidence,
    SearchEvidenceSource,
)
from app.company_intelligence.schemas import (
    CandidateSource,
    CompanyCandidate,
    RecruitmentLinkCandidate,
)
from app.company_intelligence.url_safety import normalize_url


class CanonicalMappingError(ValueError):
    """A safe deterministic mapping failure between extraction and the domain."""


class UnknownSourceReferenceError(CanonicalMappingError):
    """Stage B referenced a source ID absent from the Stage A registry."""


class UnknownUrlReferenceError(CanonicalMappingError):
    """Stage B referenced a URL ID absent from the Stage A registry."""


_COMPANY_NATURE_ALIASES = {
    "国有企业": "STATE_OWNED",
    "国企": "STATE_OWNED",
    "state-owned": "STATE_OWNED",
    "state owned": "STATE_OWNED",
    "中央企业": "CENTRAL_OWNED",
    "央企": "CENTRAL_OWNED",
    "central-owned": "CENTRAL_OWNED",
    "central owned": "CENTRAL_OWNED",
    "私营企业": "PRIVATE",
    "民营企业": "PRIVATE",
    "private": "PRIVATE",
    "private enterprise": "PRIVATE",
    "外资企业": "FOREIGN",
    "foreign": "FOREIGN",
    "foreign enterprise": "FOREIGN",
    "合资企业": "JOINT_VENTURE",
    "joint venture": "JOINT_VENTURE",
    "创业公司": "STARTUP",
    "初创公司": "STARTUP",
    "startup": "STARTUP",
}


def normalize_company_nature(value: str | None) -> str | None:
    """Map only explicit, explainable aliases to existing project values."""
    if value is None:
        return None
    normalized = " ".join(value.strip().casefold().split())
    return _COMPANY_NATURE_ALIASES.get(normalized)


def normalize_company_size(value: str | int | float | None) -> str | None:
    """Classify only explicit headcount numbers/ranges into existing size buckets."""
    if value is None:
        return None
    text = str(value).strip().casefold().replace(",", "")
    exact = {
        "50以下": "50以下",
        "50-200": "50-200",
        "200-500": "200-500",
        "500-1000": "500-1000",
        "1000-5000": "1000-5000",
        "5000以上": "5000以上",
        "10000+": "5000以上",
    }
    if text in exact:
        return exact[text]
    numbers = [int(number) for number in re.findall(r"\d+", text)]
    if len(numbers) != 1:
        return None
    headcount = numbers[0]
    if headcount < 50:
        return "50以下"
    if headcount < 200:
        return "50-200"
    if headcount < 500:
        return "200-500"
    if headcount < 1000:
        return "500-1000"
    if headcount < 5000:
        return "1000-5000"
    return "5000以上"


class KimiRawSource(BaseModel):
    """Traceable source shape emitted by Kimi as ``data_sources``."""

    url: str = Field(min_length=1, max_length=2048)
    title: str = Field(min_length=1, max_length=512)
    source_type: str = Field(min_length=1, max_length=64)
    retrieved_at: datetime
    provider: str | None = Field(default=None, max_length=64)

    model_config = ConfigDict(extra="forbid")


class KimiRawCompanyResult(BaseModel):
    """The Kimi final-content contract; it is not a persistence or domain model."""

    company_name: str = Field(min_length=1, max_length=255)
    company_aliases: list[str] = Field(default_factory=list)
    industry: str | None = Field(default=None, max_length=128)
    ownership_type: str | None = Field(default=None, max_length=64)
    website: str | None = Field(default=None, max_length=2048)
    employees: str | int | float | None = None
    business_scope: str | None = None
    data_sources: list[KimiRawSource] = Field(default_factory=list)

    legal_representative: str | None = None
    registered_capital: str | None = None
    headquarters_location: str | None = None
    stock_code: str | None = None
    listing_market: str | None = None
    listing_date: date | None = None
    major_shareholders: list[JsonValue] = Field(default_factory=list)
    ultimate_beneficial_owner: str | None = None
    senior_executives: list[JsonValue] = Field(default_factory=list)
    financial_highlights: list[JsonValue] = Field(default_factory=list)
    business_segments: list[JsonValue] = Field(default_factory=list)
    major_clients: list[JsonValue] = Field(default_factory=list)
    subsidiaries: list[JsonValue] = Field(default_factory=list)
    affiliated_companies: list[JsonValue] = Field(default_factory=list)
    qualifications: list[JsonValue] = Field(default_factory=list)
    recent_developments: list[JsonValue] = Field(default_factory=list)
    risk_factors: list[JsonValue] = Field(default_factory=list)
    data_date: date | None = None
    confidence_level: str | None = None

    model_config = ConfigDict(extra="forbid")


class KimiCompanyCandidateMapper:
    """Maps the provider contract into the single strict domain candidate contract."""

    @staticmethod
    def to_candidate(
        raw: KimiRawCompanyResult | KimiCanonicalExtractionResult,
        evidence: KimiSearchEvidence | None = None,
    ) -> CompanyCandidate:
        if isinstance(raw, KimiCanonicalExtractionResult):
            if evidence is None:
                raise ValueError("canonical extraction requires search evidence")
            return KimiCompanyCandidateMapper._from_canonical(raw, evidence)
        return CompanyCandidate(
            company_name=raw.company_name,
            short_name=raw.company_aliases[0] if raw.company_aliases else None,
            industry=raw.industry,
            company_nature=raw.ownership_type,
            company_size=str(raw.employees) if raw.employees is not None else None,
            official_website=raw.website,
            description=raw.business_scope,
            sources=[
                CandidateSource(
                    url=source.url,
                    title=source.title,
                    source_type=source.source_type,
                    provider=source.provider or "kimi",
                    retrieved_at=source.retrieved_at,
                )
                for source in raw.data_sources
            ],
        )

    @staticmethod
    def _from_canonical(
        canonical: KimiCanonicalExtractionResult, evidence: KimiSearchEvidence
    ) -> CompanyCandidate:
        sources_by_id = {source.source_id: source for source in evidence.sources}
        sources_by_url_id = {source.url_id: source for source in evidence.sources}
        sources = [
            KimiCompanyCandidateMapper._candidate_source(source, evidence)
            for source in KimiCompanyCandidateMapper._resolve_sources(
                canonical.source_ids, sources_by_id
            )
        ]
        official_website = KimiCompanyCandidateMapper._resolve_optional_url(
            canonical.official_website_url_id, sources_by_url_id
        )

        links: list[RecruitmentLinkCandidate] = []
        for link in canonical.recruitment_links:
            source = sources_by_url_id.get(link.url_id)
            if source is None:
                raise UnknownUrlReferenceError("recruitment URL ID is not in search evidence")
            links.append(
                RecruitmentLinkCandidate(
                    title=source.title,
                    url=normalize_url(source.url),
                    channel_type=link.channel_type,
                    claimed_official=link.claimed_official,
                    source_url=normalize_url(source.url),
                    evidence=link.evidence,
                )
            )

        return CompanyCandidate(
            company_name=canonical.full_name,
            short_name=canonical.short_name,
            industry=canonical.industry,
            company_nature=normalize_company_nature(canonical.company_nature_raw),
            company_size=normalize_company_size(canonical.company_size_raw),
            official_website=official_website,
            description=canonical.description,
            sources=sources,
            recruitment_links=links,
        )

    @staticmethod
    def _resolve_sources(
        source_ids: list[str], registry: dict[str, SearchEvidenceSource]
    ) -> list[SearchEvidenceSource]:
        resolved: list[SearchEvidenceSource] = []
        seen: set[str] = set()
        for source_id in source_ids:
            source = registry.get(source_id)
            if source is None:
                raise UnknownSourceReferenceError("source ID is not in search evidence")
            if source_id not in seen:
                seen.add(source_id)
                resolved.append(source)
        return resolved

    @staticmethod
    def _resolve_optional_url(
        url_id: str | None, registry: dict[str, SearchEvidenceSource]
    ) -> str | None:
        if url_id is None:
            return None
        source = registry.get(url_id)
        if source is None:
            raise UnknownUrlReferenceError("official website URL ID is not in search evidence")
        return normalize_url(source.url)

    @staticmethod
    def _candidate_source(
        source: SearchEvidenceSource, evidence: KimiSearchEvidence
    ) -> CandidateSource:
        return CandidateSource(
            title=source.title,
            url=normalize_url(source.url),
            source_type=source.source_type,
            provider=evidence.provider,
            retrieved_at=evidence.retrieved_at,
        )
