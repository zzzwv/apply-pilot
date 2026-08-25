"""Explainable official-domain verification and deterministic link ranking."""

from dataclasses import dataclass
from urllib.parse import urlsplit

from app.company_intelligence.links import HttpxLinkValidator
from app.company_intelligence.normalization import normalize_company_name
from app.company_intelligence.schemas import RecruitmentLinkCandidate
from app.models.enums import LinkStatus, VerificationStatus


@dataclass(frozen=True)
class DomainVerification:
    """A deterministic explanation for whether a link belongs to the official domain."""

    verified: bool
    reason: str


_CHANNEL_PRIORITY = {
    "official_campus": 0,
    "official_internship": 1,
    "official_social": 2,
    "announcement": 3,
    "third_party": 4,
}


def resolve_official_domain(
    *,
    company_name: str,
    candidate: RecruitmentLinkCandidate,
    official_website: str | None,
) -> DomainVerification:
    """Verify only the link's relation to a known official website and visible title evidence."""
    normalized_name = normalize_company_name(company_name)
    if normalized_name not in normalize_company_name(candidate.title):
        return DomainVerification(False, "company name is not present in the link title")
    if official_website is None:
        return DomainVerification(False, "no official website domain is available for verification")

    candidate_host = urlsplit(candidate.url).hostname
    official_host = urlsplit(official_website).hostname
    candidate_domain = _without_leading_www(candidate_host)
    official_domain = _without_leading_www(official_host)
    domains_match = candidate_domain is not None and official_domain is not None and (
        candidate_domain == official_domain
        or candidate_domain.endswith(f".{official_domain}")
    )
    if domains_match:
        return DomainVerification(True, "link domain matches the official website domain")
    return DomainVerification(False, "link domain does not match the official website domain")


def _without_leading_www(hostname: str | None) -> str | None:
    """Treat only the conventional leading www label as equivalent to an official host."""
    if hostname is None:
        return None
    return hostname[4:] if hostname.startswith("www.") else hostname


async def verify_recruitment_link(
    *,
    candidate: RecruitmentLinkCandidate,
    company_name: str,
    official_website: str | None,
    validator: HttpxLinkValidator,
) -> RecruitmentLinkCandidate:
    """Return a copied candidate with HTTP and official-domain evidence, preserving its source."""
    checked = await validator.validate(candidate.url)
    domain = resolve_official_domain(
        company_name=company_name,
        candidate=candidate,
        official_website=official_website,
    )
    evidence = "; ".join(part for part in (candidate.evidence, domain.reason) if part)

    if checked.status is LinkStatus.VALID and domain.verified:
        verification_status = VerificationStatus.VERIFIED
    elif checked.status is LinkStatus.INVALID:
        verification_status = VerificationStatus.REJECTED
    elif checked.status is LinkStatus.VALID:
        verification_status = VerificationStatus.CANDIDATE
    else:
        verification_status = VerificationStatus.UNVERIFIED

    return candidate.model_copy(
        update={
            "valid_status": checked.status,
            "http_status": checked.http_status,
            "final_url": checked.final_url,
            "verification_status": verification_status,
            "evidence": evidence,
        }
    )


def rank_recruitment_links(
    links: list[RecruitmentLinkCandidate],
) -> list[RecruitmentLinkCandidate]:
    """Sort recruitment links by official channel before stable human-readable tie-breakers."""
    return sorted(
        links,
        key=lambda link: (
            _CHANNEL_PRIORITY.get(link.channel_type, len(_CHANNEL_PRIORITY)),
            link.url.casefold(),
            link.title.casefold(),
        ),
    )
