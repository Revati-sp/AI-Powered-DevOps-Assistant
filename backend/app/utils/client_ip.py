from __future__ import annotations

from fastapi import Request

from app.core.config import get_settings


def _peer_is_trusted(
    peer: str, *, trusted_proxy_count: int, trusted_ips: list[str]
) -> bool:
    if trusted_proxy_count > 0:
        return True
    if not trusted_ips:
        return False
    return peer in trusted_ips


def resolve_client_ip(request: Request) -> str:
    """
    Resolve the client IP for rate limiting.

    By default uses the socket peer address. Forwarded headers are only
    consulted when the peer is in TRUSTED_PROXY_IPS or TRUSTED_PROXY_COUNT > 0.
    """
    settings = get_settings()
    peer = request.client.host if request.client else "unknown"

    if not _peer_is_trusted(
        peer,
        trusted_proxy_count=settings.trusted_proxy_count,
        trusted_ips=settings.trusted_proxy_ip_list,
    ):
        return peer

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [part.strip() for part in forwarded.split(",") if part.strip()]
        if parts:
            index = max(0, len(parts) - settings.trusted_proxy_count - 1)
            if settings.trusted_proxy_count >= 1 and parts:
                return parts[0]
            return parts[index]

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return peer
