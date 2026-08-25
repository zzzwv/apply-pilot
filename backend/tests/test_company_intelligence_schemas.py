from datetime import datetime, timezone

import pytest
from pydantic import ValidationError


def test_normalize_company_name_collapses_unicode_whitespace_and_case() -> None:
    """Protects lookups from treating equivalent Unicode input as different companies."""
    from app.company_intelligence.normalization import normalize_company_name

    assert normalize_company_name("  Ｔｅｎｃｅｎｔ　科技\t有限公司  ") == "tencent 科技 有限公司"


def test_candidate_parses_structured_data_and_preserves_source_traceability() -> None:
    """Protects network candidates from losing their normalized evidence and trust state."""
    from app.company_intelligence.schemas import CompanyCandidate
    from app.models.enums import VerificationStatus

    candidate = CompanyCandidate.model_validate(
        {
            "company_name": "  腾讯　科技有限公司 ",
            "short_name": "腾讯",
            "industry": "互联网",
            "company_nature": "民营",
            "company_size": "10000+",
            "official_website": " HTTPS://WWW.EXAMPLE.COM/careers#top ",
            "description": "招聘信息候选",
            "verification_status": "candidate",
            "recruitment_links": [
                {
                    "title": "校园招聘",
                    "url": "https://jobs.example.com/campus#openings",
                    "channel_type": "official_campus",
                    "claimed_official": True,
                    "source_url": "https://www.example.com/careers#source",
                    "evidence": "官网招聘入口",
                    "confidence": 0.9,
                }
            ],
            "sources": [
                {
                    "url": "https://www.example.com/about#company",
                    "title": "公司介绍",
                    "source_type": "official_site",
                    "provider": "kimi",
                    "retrieved_at": "2026-08-25T12:30:00Z",
                }
            ],
        }
    )

    assert candidate.company_name == "腾讯 科技有限公司"
    assert candidate.official_website == "https://www.example.com/careers"
    assert candidate.verification_status is VerificationStatus.CANDIDATE
    assert candidate.recruitment_links[0].url == "https://jobs.example.com/campus"
    assert candidate.sources[0].url == "https://www.example.com/about"
    assert candidate.sources[0].title == "公司介绍"
    assert candidate.sources[0].source_type == "official_site"
    assert candidate.sources[0].provider == "kimi"
    assert candidate.sources[0].retrieved_at == datetime(2026, 8, 25, 12, 30, tzinfo=timezone.utc)


def test_candidate_schema_forbids_unknown_fields() -> None:
    """Protects structured candidate parsing from silently accepting model-invented fields."""
    from app.company_intelligence.schemas import CompanyCandidate

    with pytest.raises(ValidationError):
        CompanyCandidate.model_validate(
            {
                "company_name": "腾讯科技有限公司",
                "sources": [],
                "unexpected_fact": "do not trust this",
            }
        )
