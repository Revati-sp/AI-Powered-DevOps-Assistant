import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match

from app.api.routes import (
    admin_providers,
    artifacts,
    auth,
    chat,
    dashboard,
    generators,
    health,
    invitations,
    logs,
    org_providers,
    organizations,
    policies,
    reviews,
    tasks,
    usage,
    users,
)
from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppError, RateLimitError
from app.core.logging import get_logger, setup_logging
from app.core.metrics import record_http_request, record_rate_limit_rejection
from app.core.observability import init_observability, shutdown_observability
from app.core.security_headers import security_headers_middleware
from app.schemas.common import ErrorDetail, ErrorResponse

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.debug)
    settings.validate_production_secrets()
    init_observability(settings, app=app)
    logger.info("Starting %s (%s)", settings.app_name, settings.app_env)
    yield
    shutdown_observability()
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.openapi_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Any:
        handler = security_headers_middleware(settings)
        return await handler(request, call_next)


if settings.security_headers_enabled:
    app.add_middleware(SecurityHeadersMiddleware)


def _resolve_route_template(request: Request) -> str:
    for route in app.routes:
        match, _ = route.matches(request.scope)
        if match == Match.FULL:
            path = getattr(route, "path", None)
            if path:
                return str(path)
    return request.url.path


def _request_id_from(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _details_with_request_id(
    request: Request, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    merged = dict(details or {})
    request_id = _request_id_from(request)
    if request_id and "request_id" not in merged:
        merged["request_id"] = request_id
    return merged


@app.middleware("http")
async def request_context_middleware(request: Request, call_next: Any) -> Any:
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    duration = time.perf_counter() - start
    route = _resolve_route_template(request)
    if route not in {"/health", "/ready", "/metrics"}:
        record_http_request(
            method=request.method,
            route=route,
            status_code=response.status_code,
            duration_seconds=duration,
        )
    return response


@app.middleware("http")
async def request_size_limit_middleware(request: Request, call_next: Any) -> Any:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
        except ValueError:
            size = 0
        max_bytes = settings.max_json_body_size_bytes
        if size > max_bytes:
            return JSONResponse(
                status_code=413,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code=ErrorCode.PAYLOAD_TOO_LARGE,
                        message="Request body exceeds configured limit.",
                        details=_details_with_request_id(
                            request,
                            {"max_json_body_size_bytes": max_bytes},
                        ),
                    )
                ).model_dump(),
            )
    return await call_next(request)


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=code, message=message, details=details or {})
        ).model_dump(),
        headers=headers,
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    headers: dict[str, str] = {}
    if isinstance(exc, RateLimitError):
        category = str(exc.details.get("category", "api"))
        record_rate_limit_rejection(category)
        retry_after = exc.details.get("retry_after_seconds")
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)
        if "limit" in exc.details:
            headers["X-RateLimit-Limit"] = str(exc.details["limit"])
        if "remaining" in exc.details:
            headers["X-RateLimit-Remaining"] = str(exc.details["remaining"])
        if "reset_seconds" in exc.details:
            headers["X-RateLimit-Reset"] = str(exc.details["reset_seconds"])

    return _error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=_details_with_request_id(request, exc.details),
        headers=headers or None,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error_response(
        status_code=422,
        code=ErrorCode.VALIDATION_ERROR,
        message="Invalid request",
        details=_details_with_request_id(request, {"errors": exc.errors()}),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = ErrorCode.HTTP_ERROR
    if exc.status_code == 401:
        code = ErrorCode.UNAUTHORIZED
    elif exc.status_code == 403:
        code = ErrorCode.FORBIDDEN
    elif exc.status_code == 404:
        code = ErrorCode.NOT_FOUND
    return _error_response(
        status_code=exc.status_code,
        code=code,
        message=str(exc.detail),
        details=_details_with_request_id(request),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc.__class__.__name__)
    return _error_response(
        status_code=500,
        code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred.",
        details=_details_with_request_id(request),
    )


api_prefix = settings.api_v1_prefix
app.include_router(health.router)
app.include_router(auth.router, prefix=api_prefix)
app.include_router(users.router, prefix=api_prefix)
app.include_router(chat.router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)
app.include_router(logs.router, prefix=api_prefix)
app.include_router(tasks.router, prefix=api_prefix)
app.include_router(generators.router, prefix=api_prefix)
app.include_router(reviews.router, prefix=api_prefix)
app.include_router(artifacts.router, prefix=api_prefix)
app.include_router(policies.router, prefix=api_prefix)
app.include_router(policies.audit_router, prefix=api_prefix)
app.include_router(organizations.router, prefix=api_prefix)
app.include_router(invitations.router, prefix=api_prefix)
app.include_router(admin_providers.router, prefix=api_prefix)
app.include_router(org_providers.router, prefix=api_prefix)
app.include_router(usage.router, prefix=api_prefix)
