import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import SplitResult, urlsplit, urlunsplit


class UnsafeUrlError(ValueError):
    """Raised when a URL is unsuitable for an outbound HTTP request."""


@dataclass(frozen=True)
class SafeUrlResolution:
    """A URL plus the public IPs approved for its next outbound connection."""

    url: str
    hostname: str
    approved_ips: tuple[str, ...]

    def allows_peer(self, peer_ip: str) -> bool:
        """Return whether an HTTP client's connected peer matches this DNS resolution."""
        try:
            return str(ipaddress.ip_address(peer_ip)) in self.approved_ips
        except ValueError:
            return False


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

    try:
        hostname = parsed.hostname.rstrip(".")
        if not hostname:
            raise ValueError("URL has an invalid host")
        hostname = hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as error:
        raise ValueError("URL has an invalid host") from error

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


def _resolve_public_ips(hostname: str) -> tuple[str, ...]:
    host = hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise UnsafeUrlError("URL host is not public")

    try:
        addresses = [str(ipaddress.ip_address(host))]
    except ValueError:
        try:
            results = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            addresses = [result[4][0] for result in results]
        except OSError as error:
            raise UnsafeUrlError("URL host could not be resolved") from error

    try:
        normalized_ips = (str(ipaddress.ip_address(address)) for address in addresses)
        public_ips = tuple(dict.fromkeys(normalized_ips))
    except ValueError as error:
        raise UnsafeUrlError("URL host resolved to an invalid address") from error
    if not public_ips or any(not ipaddress.ip_address(address).is_global for address in public_ips):
        raise UnsafeUrlError("URL host resolved to a non-public address")
    return public_ips


def resolve_safe_url(value: str) -> SafeUrlResolution:
    """Resolve a URL once and retain the public IPs a caller must pin or verify."""
    normalized_url = normalize_url(value)
    hostname = urlsplit(normalized_url).hostname
    if hostname is None:
        raise UnsafeUrlError("URL must include a host")

    return SafeUrlResolution(
        url=normalized_url,
        hostname=hostname,
        approved_ips=_resolve_public_ips(hostname),
    )


def is_safe_url(value: str) -> bool:
    """Return whether resolving an HTTP URL produces only public network addresses."""
    try:
        resolve_safe_url(value)
    except (UnsafeUrlError, ValueError):
        return False
    return True


def validate_safe_url(value: str) -> SafeUrlResolution:
    """Return a pinned-resolution contract before each request or redirect hop."""
    return resolve_safe_url(value)
