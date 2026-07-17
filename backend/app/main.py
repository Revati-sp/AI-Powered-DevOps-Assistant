from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import auth, chat, generators, health, logs, reviews, users
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger, setup_logging
from app.schemas.common import ErrorDetail, ErrorResponse

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.debug)
    logger.info("Starting %s (%s)", settings.app_name, settings.app_env)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_size_and_rate_limit_hooks(request: Request, call_next: Any) -> Any:
    """
    Lightweight request guardrails.

    Ready for a Redis-backed rate limiter without changing route handlers.
    """
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
        except ValueError:
            size = 0
        max_bytes = settings.max_request_body_mb * 1024 * 1024
        if size > max_bytes:
            return JSONResponse(
                status_code=413,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="PAYLOAD_TOO_LARGE",
                        message="Request body exceeds configured limit.",
                        details={"max_request_body_mb": settings.max_request_body_mb},
                    )
                ).model_dump(),
            )

    # Placeholder for distributed rate limiting keyed by user/IP.
    request.state.rate_limit_bucket = (
        request.client.host if request.client else "unknown"
    )
    return await call_next(request)


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=code, message=message, details=details or {})
        ).model_dump(),
    )


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Invalid request",
        details={"errors": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = "HTTP_ERROR"
    if exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 404:
        code = "NOT_FOUND"
    return _error_response(
        status_code=exc.status_code,
        code=code,
        message=str(exc.detail),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc.__class__.__name__)
    return _error_response(
        status_code=500,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
    )


api_prefix = settings.api_v1_prefix
app.include_router(health.router)
app.include_router(auth.router, prefix=api_prefix)
app.include_router(users.router, prefix=api_prefix)
app.include_router(chat.router, prefix=api_prefix)
app.include_router(logs.router, prefix=api_prefix)
app.include_router(generators.router, prefix=api_prefix)
app.include_router(reviews.router, prefix=api_prefix)
