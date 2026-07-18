from typing import Any

from app.core.error_codes import ErrorCode


class AppError(Exception):
    """Base application error with structured API details."""

    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.APP_ERROR,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        super().__init__(message, code=ErrorCode.NOT_FOUND, status_code=404, **kwargs)


class UnauthorizedError(AppError):
    def __init__(
        self,
        message: str = "Unauthorized",
        *,
        code: str = ErrorCode.INVALID_CREDENTIALS,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, status_code=401, **kwargs)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", **kwargs: Any) -> None:
        super().__init__(message, code=ErrorCode.FORBIDDEN, status_code=403, **kwargs)


class ValidationAppError(AppError):
    def __init__(self, message: str = "Invalid request", **kwargs: Any) -> None:
        super().__init__(
            message, code=ErrorCode.VALIDATION_ERROR, status_code=422, **kwargs
        )


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict", **kwargs: Any) -> None:
        super().__init__(message, code=ErrorCode.CONFLICT, status_code=409, **kwargs)


class LLMProviderError(AppError):
    def __init__(
        self,
        message: str = "LLM provider request failed",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=ErrorCode.LLM_ERROR, status_code=502, **kwargs)


class RateLimitError(AppError):
    def __init__(
        self,
        message: str = "Too many requests. Try again later.",
        *,
        code: str = ErrorCode.RATE_LIMIT_EXCEEDED,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, status_code=429, **kwargs)


class QuotaExceededError(AppError):
    def __init__(
        self,
        message: str = "Usage quota exceeded.",
        *,
        code: str = ErrorCode.QUOTA_EXCEEDED,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, status_code=429, **kwargs)
