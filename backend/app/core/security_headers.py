from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from app.core.config import Settings

API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


def build_security_headers(settings: Settings) -> dict[str, str]:
    """Return security response headers appropriate for a JSON API."""
    headers = {
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "interest-cohort=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Content-Security-Policy": API_CSP,
    }

    if settings.hsts_enabled and settings.is_production:
        directives = [f"max-age={settings.hsts_max_age_seconds}"]
        if settings.hsts_include_subdomains:
            directives.append("includeSubDomains")
        if settings.hsts_preload:
            directives.append("preload")
        headers["Strict-Transport-Security"] = "; ".join(directives)

    return headers


def security_headers_middleware(
    settings: Settings,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    """Attach standard security headers to every HTTP response."""

    headers = build_security_headers(settings)

    async def middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        if settings.security_headers_enabled:
            for name, value in headers.items():
                if name not in response.headers:
                    response.headers[name] = value
        return response

    return middleware
