"""Safe, bounded HTTP validation and recruitment-link discovery."""

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Callable
from urllib.parse import urljoin, urlsplit

import httpx

from app.company_intelligence.schemas import RecruitmentLinkCandidate
from app.company_intelligence.url_safety import (
    SafeUrlResolution,
    UnsafeUrlError,
    normalize_url,
    resolve_safe_url,
)
from app.models.enums import LinkStatus

Resolver = Callable[[str], SafeUrlResolution]

CAREER_KEYWORDS = (
    "career",
    "careers",
    "job",
    "jobs",
    "hiring",
    "recruit",
    "campus",
    "graduate",
    "intern",
    "招聘",
    "校招",
    "实习",
    "职位",
    "人才",
)


@dataclass(frozen=True)
class ValidatedLink:
    """The safe-to-display outcome of one bounded HTTP link validation."""

    status: LinkStatus
    http_status: int | None
    final_url: str
    reason: str
    content: str = ""


class _AnchorParser(HTMLParser):
    """Extract only anchor text and href values; this parser never follows a link."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a" or self._href is not None:
            return
        attributes = dict(attrs)
        href = attributes.get("href")
        if href:
            self._href = href
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._parts).strip()))
            self._href = None
            self._parts = []


class HttpxLinkValidator:
    """Validate URLs while checking the peer selected by HTTPX against DNS approval."""

    def __init__(
        self,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        resolver: Resolver = resolve_safe_url,
        timeout_seconds: float = 5,
        max_redirects: int = 3,
    ) -> None:
        self._transport = transport
        self._resolver = resolver
        self._timeout_seconds = timeout_seconds
        self._max_redirects = max_redirects

    async def validate(self, url: str) -> ValidatedLink:
        """Fetch a URL with every redirect and connected peer checked before use."""
        async with httpx.AsyncClient(
            transport=self._transport,
            timeout=httpx.Timeout(self._timeout_seconds),
            follow_redirects=False,
            trust_env=False,
        ) as client:
            current_url = url
            redirects = 0
            while True:
                try:
                    resolution = self._resolver(current_url)
                except (UnsafeUrlError, ValueError):
                    reason = "redirect target is unsafe" if redirects else "URL is unsafe"
                    return ValidatedLink(LinkStatus.UNKNOWN, None, current_url, reason)

                try:
                    response = await client.get(resolution.url)
                except httpx.TimeoutException:
                    return ValidatedLink(
                        LinkStatus.UNKNOWN,
                        None,
                        resolution.url,
                        "request timed out",
                    )
                except httpx.TransportError:
                    return ValidatedLink(
                        LinkStatus.UNKNOWN,
                        None,
                        resolution.url,
                        "request failed",
                    )

                if not resolution.allows_peer(_connected_peer(response)):
                    return ValidatedLink(
                        LinkStatus.UNKNOWN,
                        response.status_code,
                        resolution.url,
                        "connected peer was not approved",
                    )

                location = response.headers.get("location")
                if 300 <= response.status_code < 400 and location:
                    if redirects >= self._max_redirects:
                        return ValidatedLink(
                            LinkStatus.UNKNOWN,
                            response.status_code,
                            resolution.url,
                            "too many redirects",
                        )
                    current_url = urljoin(resolution.url, location)
                    redirects += 1
                    continue

                return ValidatedLink(
                    _status_for_http_code(response.status_code),
                    response.status_code,
                    resolution.url,
                    _reason_for_http_code(response.status_code),
                    response.text,
                )


def _connected_peer(response: httpx.Response) -> str:
    """Return the actual TCP peer exposed by HTTPX/httpcore, or an empty unsafe value."""
    peer = response.extensions.get("connected_peer")
    if isinstance(peer, str):
        return peer
    if isinstance(peer, tuple) and peer and isinstance(peer[0], str):
        return peer[0]

    stream = response.extensions.get("network_stream")
    if stream is None:
        return ""
    try:
        peer = stream.get_extra_info("server_addr")
    except (AttributeError, OSError):
        return ""
    if isinstance(peer, tuple) and peer and isinstance(peer[0], str):
        return peer[0]
    return peer if isinstance(peer, str) else ""


def _status_for_http_code(status_code: int) -> LinkStatus:
    if 200 <= status_code < 400:
        return LinkStatus.VALID
    if status_code in {404, 410}:
        return LinkStatus.INVALID
    return LinkStatus.UNKNOWN


def _reason_for_http_code(status_code: int) -> str:
    if 200 <= status_code < 400:
        return "HTTP response is reachable"
    if status_code in {404, 410}:
        return "HTTP response says the page is unavailable"
    if status_code in {403, 429}:
        return "HTTP response does not establish link availability"
    return "HTTP response is inconclusive"


def _is_career_candidate(title: str, url: str) -> bool:
    lower_value = f"{title} {url}".casefold()
    return any(keyword in lower_value for keyword in CAREER_KEYWORDS)


def _extract_career_candidates(
    html: str,
    *,
    source_url: str,
    homepage_host: str,
) -> list[RecruitmentLinkCandidate]:
    parser = _AnchorParser()
    parser.feed(html)
    parser.close()

    candidates: list[RecruitmentLinkCandidate] = []
    for href, title in parser.links:
        destination = urljoin(source_url, href)
        if not _is_career_candidate(title, destination):
            continue
        try:
            normalized_url = normalize_url(destination)
        except ValueError:
            continue
        is_official = urlsplit(normalized_url).hostname == homepage_host
        candidates.append(
            RecruitmentLinkCandidate(
                title=title or normalized_url,
                url=normalized_url,
                channel_type=_channel_for(title, normalized_url, is_official),
                claimed_official=is_official,
                source_url=source_url,
                evidence="career keyword link discovered from a bounded official-page scan",
            )
        )
    return candidates


def _channel_for(title: str, url: str, is_official: bool) -> str:
    value = f"{title} {url}".casefold()
    if is_official and any(keyword in value for keyword in ("campus", "graduate", "校招")):
        return "official_campus"
    if is_official and any(keyword in value for keyword in ("intern", "实习")):
        return "official_internship"
    if is_official:
        return "official_social"
    if "announcement" in value or "公告" in value:
        return "announcement"
    return "third_party"


async def discover_recruitment_links(
    *,
    homepage_url: str,
    company_name: str,
    validator: HttpxLinkValidator,
) -> list[RecruitmentLinkCandidate]:
    """Inspect a homepage and at most one same-host careers page, without crawling further."""
    homepage = await validator.validate(homepage_url)
    if homepage.status is not LinkStatus.VALID:
        return []

    homepage_host = urlsplit(homepage.final_url).hostname
    if homepage_host is None:
        return []
    discovered = _extract_career_candidates(
        homepage.content,
        source_url=homepage.final_url,
        homepage_host=homepage_host,
    )

    internal_career_page = next(
        (
            candidate
            for candidate in discovered
            if urlsplit(candidate.url).hostname == homepage_host
            and candidate.url != homepage.final_url
        ),
        None,
    )
    if internal_career_page is not None:
        career_page = await validator.validate(internal_career_page.url)
        if career_page.status is LinkStatus.VALID:
            discovered.extend(
                _extract_career_candidates(
                    career_page.content,
                    source_url=career_page.final_url,
                    homepage_host=homepage_host,
                )
            )

    del company_name  # The company is context for callers; discovery is keyword-bound only.
    unique: dict[str, RecruitmentLinkCandidate] = {}
    for candidate in discovered:
        unique.setdefault(candidate.url, candidate)
    return list(unique.values())
