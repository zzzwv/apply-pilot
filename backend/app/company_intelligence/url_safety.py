import ipaddress
import socket
from urllib.parse import SplitResult, urlsplit, urlunsplit


class UnsafeUrlError(ValueError):
    """Raised when a URL is unsuitable for an outbound HTTP request."""


def normalize_url(value: str) -> str:
    """Canonicalize a web URL for comparisons while dropping its fragment."""
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except ValueError as error:
        raise ValueError("URL has an invalid port") from error

    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must use http or https and include a host")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL must not include user credentials")

    hostname = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    host = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None and (parsed.scheme.lower(), port) not in {("http", 80), ("https", 443)}:
        host = f"{host}:{port}"

    normalized = SplitResult(
        scheme=parsed.scheme.lower(),
        netloc=host,
        path=parsed.path,
        query=parsed.query,
        fragment="",
    )
    return urlunsplit(normalized)


def _is_public_address(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return address.is_global


def _is_safe_host(hostname: str) -> bool:
    host = hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        return False

    try:
        return _is_public_address(host)
    except ValueError:
        pass

    try:
        addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError:
        return False

    return bool(addresses) and all(_is_public_address(address[4][0]) for address in addresses)


def is_safe_url(value: str) -> bool:
    """Return whether an HTTP URL resolves only to public network addresses."""
    try:
        normalized = normalize_url(value)
        hostname = urlsplit(normalized).hostname
    except ValueError:
        return False

    return hostname is not None and _is_safe_host(hostname)


def validate_safe_url(value: str) -> str:
    """Normalize and validate a URL before each request or redirect hop."""
    normalized = normalize_url(value)
    if not is_safe_url(normalized):
        raise UnsafeUrlError("URL target is not safe for outbound HTTP requests")
    return normalized
