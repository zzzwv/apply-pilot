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
