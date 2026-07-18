from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request, Response

from app.api.dependencies import get_current_user
from app.core.rate_limit import RateLimitCategory, get_rate_limiter
from app.models.user import User
from app.utils.client_ip import resolve_client_ip


def _apply_headers(
    response: Response, *, limit: int, remaining: int, reset: int
) -> None:
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset)


def rate_limit_dependency(
    category: RateLimitCategory,
    *,
    authenticated: bool,
) -> Callable[..., object]:
    if authenticated:

        async def _authenticated_limit(
            request: Request,
            response: Response,
            user: Annotated[User, Depends(get_current_user)],
        ) -> RateLimitCategory:
            result = await get_rate_limiter().enforce(category, f"user:{user.id}")
            _apply_headers(
                response,
                limit=result.limit,
                remaining=result.remaining,
                reset=result.reset_seconds,
            )
            request.state.rate_limit_result = result
            return category

        return _authenticated_limit

    async def _ip_limit(request: Request, response: Response) -> RateLimitCategory:
        identity = f"ip:{resolve_client_ip(request)}"
        result = await get_rate_limiter().enforce(category, identity)
        _apply_headers(
            response,
            limit=result.limit,
            remaining=result.remaining,
            reset=result.reset_seconds,
        )
        request.state.rate_limit_result = result
        return category

    return _ip_limit


AuthRateLimit = Annotated[
    RateLimitCategory,
    Depends(rate_limit_dependency(RateLimitCategory.AUTH, authenticated=False)),
]
APIRateLimit = Annotated[
    RateLimitCategory,
    Depends(rate_limit_dependency(RateLimitCategory.API, authenticated=True)),
]
LLMRateLimit = Annotated[
    RateLimitCategory,
    Depends(rate_limit_dependency(RateLimitCategory.LLM, authenticated=True)),
]
StreamRateLimit = Annotated[
    RateLimitCategory,
    Depends(rate_limit_dependency(RateLimitCategory.STREAM, authenticated=True)),
]
UploadRateLimit = Annotated[
    RateLimitCategory,
    Depends(rate_limit_dependency(RateLimitCategory.UPLOAD, authenticated=True)),
]
