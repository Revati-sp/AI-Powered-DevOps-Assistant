from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def validate_llm_base_url(base_url: str, *, provider: str) -> str:
    """
    Validate and normalize an LLM provider base URL.

    Residual SSRF limits:
    - DNS rebinding between validation and request is not prevented.
    - Redirect following is disabled at the HTTP client layer; a 3xx to a
      private target still returns without following.
    - Time-of-check/time-of-use gaps remain for long-lived clients.
    - IPv6 ULA and some carrier-grade NAT ranges may require explicit allowlists.
    """
    settings = get_settings()
    cleaned = base_url.strip().rstrip("/")
    if not cleaned:
        raise ValidationAppError(
            f"{provider} base URL is not configured.",
            details={"provider": provider},
        )

    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"}:
        raise ValidationAppError(
            f"Invalid {provider} base URL scheme.",
            details={"provider": provider},
        )
    if parsed.username or parsed.password:
        raise ValidationAppError(
            f"{provider} base URL must not contain credentials.",
            details={"provider": provider},
        )
    if not parsed.netloc:
        raise ValidationAppError(
            f"Invalid {provider} base URL host.",
            details={"provider": provider},
        )
    if parsed.fragment:
        raise ValidationAppError(
            f"{provider} base URL must not contain a fragment.",
            details={"provider": provider},
        )

    host = (parsed.hostname or "").lower()
    is_local = host in _LOCAL_HOSTS
    if parsed.scheme == "http":
        if not settings.allow_insecure_llm_http:
            raise ValidationAppError(
                f"{provider} base URL must use https "
                "(set ALLOW_INSECURE_LLM_HTTP=true for local development).",
                details={"provider": provider},
            )
        if not is_local and settings.app_env == "production":
            raise ValidationAppError(
                f"{provider} insecure HTTP is only allowed for localhost.",
                details={"provider": provider},
            )

    _validate_host(host, provider=provider, is_local=is_local)

    return cleaned


def _validate_host(host: str, *, provider: str, is_local: bool) -> None:
    settings = get_settings()
    allowed_hosts = settings.allowed_llm_host_list
    if allowed_hosts and host not in allowed_hosts:
        raise ValidationAppError(
            f"{provider} base URL host is not in the configured allowlist.",
            details={"provider": provider, "host": host},
        )

    if is_local and settings.allow_insecure_llm_http:
        return

    if settings.allow_private_llm_networks:
        return

    literal_ip: ipaddress.IPv4Address | ipaddress.IPv6Address | None = None
    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None

    if literal_ip is not None:
        _reject_blocked_address(literal_ip, provider=provider, is_local=is_local)
        return

    try:
        addr_infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValidationAppError(
            f"Unable to resolve {provider} base URL host.",
            details={"provider": provider, "host": host},
        ) from exc

    seen: set[str] = set()
    for info in addr_infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        ip_str = str(sockaddr[0])
        if ip_str in seen:
            continue
        seen.add(ip_str)
        try:
            resolved = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        _reject_blocked_address(resolved, provider=provider, is_local=is_local)


def _reject_blocked_address(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
    *,
    provider: str,
    is_local: bool,
) -> None:
    settings = get_settings()
    if is_local and (
        settings.allow_private_llm_networks or settings.allow_insecure_llm_http
    ):
        return

    if (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise ValidationAppError(
            f"{provider} base URL must not target private or restricted networks.",
            details={"provider": provider, "address": str(address)},
        )


def chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"
