"""Patched url_validation.py — allows private/internal IPs for Docker-internal MCP URLs."""

import ipaddress
import socket
from urllib.parse import urlparse

_BLOCKED_HOSTNAMES = {
    "metadata.google.internal",
    "metadata.google.internal.",
}

_BLOCKED_SUFFIXES = (
    ".local",
    ".localdomain",
    ".home.arpa",
)


def _normalize_hostname(hostname: str) -> str:
    return hostname.rstrip(".").lower()


def _is_blocked_hostname(hostname: str) -> bool:
    normalized = _normalize_hostname(hostname)
    blocked_hostnames = {_normalize_hostname(value) for value in _BLOCKED_HOSTNAMES}
    return normalized in blocked_hostnames or any(normalized.endswith(suffix) for suffix in _BLOCKED_SUFFIXES)


def validate_mcp_server_url(url: str, *, resolve_hostname: bool = True) -> str:
    """Validate MCP HTTP(S) URLs — allows private IPs for internal Docker networking."""
    if not url:
        raise ValueError("server_url cannot be empty")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"server_url must start with 'http://' or 'https://', got: '{url}'")
    if not parsed.netloc:
        raise ValueError(f"server_url must have a valid host, got: '{url}'")
    if parsed.hostname is None:
        raise ValueError("Missing hostname")

    hostname = _normalize_hostname(parsed.hostname)
    if _is_blocked_hostname(hostname):
        raise ValueError(f"Blocked internal hostname: {parsed.hostname}")

    try:
        ipaddress.ip_address(hostname)
        return url
    except ValueError:
        pass

    if not resolve_hostname:
        return url

    try:
        infos = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise ValueError(f"Cannot resolve hostname: {parsed.hostname}") from exc

    if not infos:
        raise ValueError(f"Cannot resolve hostname: {parsed.hostname}")

    return url
