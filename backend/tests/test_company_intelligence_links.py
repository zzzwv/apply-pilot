import httpx
import pytest

PUBLIC_IP = "93.184.216.34"


def safe_resolution(url: str):
    """Use a stable public peer so link tests never resolve or contact the Internet."""
    from app.company_intelligence.url_safety import SafeUrlResolution, normalize_url

    normalized = normalize_url(url)
    return SafeUrlResolution(
        url=normalized,
        hostname=httpx.URL(normalized).host,
        approved_ips=(PUBLIC_IP,),
    )


def mock_response(
    status_code: int,
    *,
    headers: dict[str, str] | None = None,
    html: str = "",
) -> httpx.Response:
    """Return an HTTPX response with a peer observable by the validator."""
    return httpx.Response(
        status_code,
        headers=headers,
        text=html,
        extensions={"connected_peer": PUBLIC_IP},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "expected_status"),
    [
        (200, "valid"),
        (301, "valid"),
        (404, "invalid"),
        (410, "invalid"),
        (403, "unknown"),
        (429, "unknown"),
    ],
)
async def test_httpx_validator_maps_http_statuses_to_link_status(
    status_code: int,
    expected_status: str,
) -> None:
    """Protects recruitment previews from treating access controls as broken links."""
    from app.company_intelligence.links import HttpxLinkValidator

    validator = HttpxLinkValidator(
        transport=httpx.MockTransport(lambda _request: mock_response(status_code)),
        resolver=safe_resolution,
    )

    result = await validator.validate("https://www.example.com/careers")

    assert result.status.value == expected_status
    assert result.http_status == status_code
    assert result.final_url == "https://www.example.com/careers"


@pytest.mark.asyncio
async def test_httpx_validator_reports_timeout_as_unknown() -> None:
    """Protects temporary network failures from being presented as invalid recruitment pages."""
    from app.company_intelligence.links import HttpxLinkValidator

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    validator = HttpxLinkValidator(
        transport=httpx.MockTransport(timeout), resolver=safe_resolution
    )

    result = await validator.validate("https://www.example.com/careers")

    assert result.status.value == "unknown"
    assert result.http_status is None
    assert result.reason == "request timed out"


@pytest.mark.asyncio
async def test_httpx_validator_blocks_an_unsafe_redirect_before_requesting_it() -> None:
    """Protects the actual redirect flow from DNS-validated public URLs pivoting internally."""
    from app.company_intelligence.links import HttpxLinkValidator
    from app.company_intelligence.url_safety import UnsafeUrlError

    requested_urls: list[str] = []

    def resolver(url: str):
        if "private.example" in url:
            raise UnsafeUrlError("URL host resolved to a non-public address")
        return safe_resolution(url)

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return mock_response(302, headers={"location": "http://private.example/admin"})

    validator = HttpxLinkValidator(
        transport=httpx.MockTransport(handler), resolver=resolver
    )

    result = await validator.validate("https://www.example.com/careers")

    assert result.status.value == "unknown"
    assert result.reason == "redirect target is unsafe"
    assert requested_urls == ["https://www.example.com/careers"]


@pytest.mark.asyncio
async def test_httpx_validator_rejects_a_connected_peer_outside_the_safe_resolution() -> None:
    """Protects the live HTTP flow from accepting a DNS-rebound connection after preflight."""
    from app.company_intelligence.links import HttpxLinkValidator

    validator = HttpxLinkValidator(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200, extensions={"connected_peer": "10.0.0.8"}
            )
        ),
        resolver=safe_resolution,
    )

    result = await validator.validate("https://www.example.com/careers")

    assert result.status.value == "unknown"
    assert result.reason == "connected peer was not approved"


def test_official_domain_resolution_uses_title_name_and_known_official_domain() -> None:
    """Protects an official label from being granted solely because a URL looks plausible."""
    from app.company_intelligence.schemas import RecruitmentLinkCandidate
    from app.company_intelligence.verification import resolve_official_domain

    candidate = RecruitmentLinkCandidate(
        title="Acme Corporation 2027 Campus Recruitment",
        url="https://careers.acme.example/campus",
        channel_type="official_campus",
        claimed_official=True,
        source_url="https://www.acme.example/careers",
    )

    verification = resolve_official_domain(
        company_name="Acme Corporation",
        candidate=candidate,
        official_website="https://www.acme.example",
    )

    assert verification.verified is True
    assert verification.reason == "link domain matches the official website domain"


def test_official_domain_resolution_requires_title_and_name_evidence_without_known_site() -> None:
    """Protects company-name matching when page evidence disagrees with the official label."""
    from app.company_intelligence.schemas import RecruitmentLinkCandidate
    from app.company_intelligence.verification import resolve_official_domain

    candidate = RecruitmentLinkCandidate(
        title="Independent job board",
        url="https://acme.example/jobs",
        channel_type="third_party",
        claimed_official=True,
    )

    verification = resolve_official_domain(
        company_name="Acme Corporation",
        candidate=candidate,
        official_website=None,
    )

    assert verification.verified is False
    assert verification.reason == "company name is not present in the link title"


@pytest.mark.asyncio
async def test_candidate_verifier_preserves_source_data_and_explains_its_result() -> None:
    """Protects source traceability while validation metadata is added to a preview link."""
    from app.company_intelligence.links import HttpxLinkValidator
    from app.company_intelligence.schemas import RecruitmentLinkCandidate
    from app.company_intelligence.verification import verify_recruitment_link

    candidate = RecruitmentLinkCandidate(
        title="Acme Corporation Careers",
        url="https://careers.acme.example/jobs",
        channel_type="official_social",
        claimed_official=True,
        source_url="https://www.acme.example/careers",
        evidence="listed on the company careers page",
    )
    validator = HttpxLinkValidator(
        transport=httpx.MockTransport(lambda _request: mock_response(200)),
        resolver=safe_resolution,
    )

    verified = await verify_recruitment_link(
        candidate=candidate,
        company_name="Acme Corporation",
        official_website="https://www.acme.example",
        validator=validator,
    )

    assert verified.source_url == "https://www.acme.example/careers"
    assert verified.evidence == (
        "listed on the company careers page; "
        "link domain matches the official website domain"
    )
    assert verified.valid_status.value == "valid"
    assert verified.verification_status.value == "verified"


@pytest.mark.asyncio
async def test_discovery_visits_only_homepage_and_one_internal_careers_hop() -> None:
    """Protects discovery from turning a candidate preview into an unbounded crawler."""
    from app.company_intelligence.links import HttpxLinkValidator, discover_recruitment_links

    requested_paths: list[str] = []

    pages = {
        "/": """
            <a href=\"/careers\">Careers</a>
            <a href=\"/about\">About Acme</a>
        """,
        "/careers": """
            <a href=\"/campus\">2027 Campus Recruitment</a>
            <a href=\"https://jobs.example.net/acme\">Acme internships</a>
            <a href=\"/about\">About</a>
        """,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        return mock_response(200, html=pages[request.url.path])

    validator = HttpxLinkValidator(
        transport=httpx.MockTransport(handler), resolver=safe_resolution
    )

    links = await discover_recruitment_links(
        homepage_url="https://www.example.com/",
        company_name="Acme",
        validator=validator,
    )

    assert requested_paths == ["/", "/careers"]
    assert [(link.url, link.source_url) for link in links] == [
        ("https://www.example.com/careers", "https://www.example.com/"),
        ("https://www.example.com/campus", "https://www.example.com/careers"),
        ("https://jobs.example.net/acme", "https://www.example.com/careers"),
    ]


def test_ranker_prefers_official_recruitment_channels_deterministically() -> None:
    """Protects the top recruitment suggestion from being an arbitrary third-party result."""
    from app.company_intelligence.schemas import RecruitmentLinkCandidate
    from app.company_intelligence.verification import rank_recruitment_links

    links = [
        RecruitmentLinkCandidate(
            title="Job board", url="https://jobs.example.net/acme", channel_type="third_party"
        ),
        RecruitmentLinkCandidate(
            title="Announcement",
            url="https://news.acme.example/hiring",
            channel_type="announcement",
        ),
        RecruitmentLinkCandidate(
            title="Social hiring",
            url="https://social.acme.example/jobs",
            channel_type="official_social",
        ),
        RecruitmentLinkCandidate(
            title="Internship",
            url="https://careers.acme.example/intern",
            channel_type="official_internship",
        ),
        RecruitmentLinkCandidate(
            title="Campus",
            url="https://careers.acme.example/campus",
            channel_type="official_campus",
        ),
    ]

    ranked = rank_recruitment_links(links)

    assert [link.channel_type for link in ranked] == [
        "official_campus",
        "official_internship",
        "official_social",
        "announcement",
        "third_party",
    ]
