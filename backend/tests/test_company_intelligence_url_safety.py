import socket

import pytest


def test_normalize_url_canonicalizes_scheme_host_whitespace_and_fragment() -> None:
    """Protects URL comparisons from duplicate forms of the same external link."""
    from app.company_intelligence.url_safety import normalize_url

    assert normalize_url(" HTTPS://EXAMPLE.COM/jobs?kind=campus#openings ") == (
        "https://example.com/jobs?kind=campus"
    )


@pytest.mark.parametrize(
    "url",
    ["file:///etc/passwd", "ftp://example.com/jobs", "mailto:jobs@example.com"],
)
def test_url_safety_rejects_invalid_schemes(url: str) -> None:
    """Protects fetchers from opening local files or non-web protocols."""
    from app.company_intelligence.url_safety import is_safe_url

    assert is_safe_url(url) is False


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/admin",
        "http://127.0.0.1/admin",
        "http://10.0.0.8/metadata",
        "http://169.254.169.254/latest/meta-data",
        "http://0.0.0.0/",
        "http://[::1]/admin",
    ],
)
def test_url_safety_rejects_local_and_internal_targets(url: str) -> None:
    """Protects redirect validation from SSRF targets expressed as literal addresses."""
    from app.company_intelligence.url_safety import is_safe_url

    assert is_safe_url(url) is False


def test_url_safety_rejects_hostname_resolving_to_private_address(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Protects redirect validation when a public-looking hostname resolves internally."""
    from app.company_intelligence.url_safety import is_safe_url

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.10", 0))
        ],
    )

    assert is_safe_url("https://redirect.example/path") is False


def test_url_safety_accepts_public_dns_result_without_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Protects legitimate redirect hops while keeping validation separate from HTTP I/O."""
    from app.company_intelligence.url_safety import is_safe_url

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
        ],
    )

    assert is_safe_url("https://www.example.com/careers") is True


def test_safe_resolution_retains_validated_ips_for_peer_verification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Protects HTTP clients from treating a hostname-only preflight as a DNS-rebinding defense."""
    from app.company_intelligence.url_safety import resolve_safe_url

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2606:2800:220:1:248:1893:25c8:1946", 0)),
        ],
    )

    resolution = resolve_safe_url("https://www.example.com/careers#jobs")

    assert resolution.url == "https://www.example.com/careers"
    assert resolution.hostname == "www.example.com"
    assert resolution.approved_ips == ("93.184.216.34", "2606:2800:220:1:248:1893:25c8:1946")
    assert resolution.allows_peer("93.184.216.34") is True
    assert resolution.allows_peer("10.0.0.8") is False


def test_safe_resolution_rejects_private_dns_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Protects pinning clients from retaining a mixed or private DNS answer."""
    from app.company_intelligence.url_safety import UnsafeUrlError, resolve_safe_url

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.8", 0))],
    )

    with pytest.raises(UnsafeUrlError):
        resolve_safe_url("https://redirect.example/path")


@pytest.mark.parametrize("url", ["https://./", "https://\ud800.example/"])
def test_normalize_url_rejects_empty_or_invalid_idna_host(url: str) -> None:
    """Protects candidate parsing from accepting malformed normalized hosts."""
    from app.company_intelligence.url_safety import normalize_url

    with pytest.raises(ValueError, match="invalid host"):
        normalize_url(url)
