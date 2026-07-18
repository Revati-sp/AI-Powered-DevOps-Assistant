# API Errors

All application errors return a consistent envelope:

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "details": {"request_id": "..."}
  }
}
```

The `code` field uses stable values from `app/core/error_codes.py`. Clients should branch on `code`, not HTTP status alone.

## Error codes

| Code | Typical HTTP | Source |
|---|---|---|
| `APP_ERROR` | 400 | Generic `AppError` default |
| `VALIDATION_ERROR` | 422 | Pydantic / request validation failures |
| `INVALID_CREDENTIALS` | 401 | Failed login or refresh (generic message) |
| `UNAUTHORIZED` | 401 | Missing or invalid access token |
| `FORBIDDEN` | 403 | Authenticated but not permitted (RBAC) |
| `NOT_FOUND` | 404 | Missing resource or non-leaking org probe |
| `CONFLICT` | 409 | Duplicate registration, slug conflict, etc. |
| `LLM_ERROR` | 502 | Provider timeout or upstream failure |
| `RATE_LIMIT_EXCEEDED` | 429 | Redis rate limiter |
| `INTERNAL_ERROR` | 500 | Unhandled exception |
| `PAYLOAD_TOO_LARGE` | 413 | Request body exceeds configured limit |
| `HTTP_ERROR` | varies | Unmapped Starlette HTTP exceptions |

## Exception mapping

`AppError` subclasses set both `status_code` and `code`:

- `NotFoundError` → `NOT_FOUND` / 404
- `UnauthorizedError` → `INVALID_CREDENTIALS` or `UNAUTHORIZED` / 401
- `ForbiddenError` → `FORBIDDEN` / 403
- `ValidationAppError` → `VALIDATION_ERROR` / 422
- `ConflictError` → `CONFLICT` / 409
- `LLMProviderError` → `LLM_ERROR` / 502
- `RateLimitError` → `RATE_LIMIT_EXCEEDED` / 429

## Rate limit response details

When limited, `details` may include:

```json
{
  "retry_after_seconds": 42,
  "category": "api"
}
```

Response headers: `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

## Request ID

Most error `details` objects include `request_id` matching the response header `X-Request-ID`.
