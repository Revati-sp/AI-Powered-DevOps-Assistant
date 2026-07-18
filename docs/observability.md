# Observability

The backend exposes health, readiness, Prometheus metrics, and optional OpenTelemetry tracing.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness |
| `GET /ready` | Dependency readiness (database / Redis as configured) |
| `GET /metrics` | Prometheus metrics (when enabled) |

Metrics exposure can be restricted by configuration. Documentation routes (`/docs`, `/redoc`, `/openapi.json`) can be disabled in production via `DOCS_ENABLED` / `OPENAPI_ENABLED`.

## OpenTelemetry

When enabled, the app instruments FastAPI, HTTPX, SQLAlchemy, Redis, and Celery with the OTLP HTTP exporter.

Safe attribute rules:

- Do not attach prompts, passwords, tokens, or uploaded log bodies to spans.
- Prefer resource IDs, provider names, route templates, and status codes.

Exporter failures must not crash request handling.

## Metrics label safety

Use low-cardinality labels (route template, method, status class, provider name). Do not label metrics with user IDs, prompts, or raw filenames.

## Request correlation

Structured error responses include a request ID when available. Prefer that ID when correlating client failures with sanitized server logs.

## Related docs

- [Operations](operations.md) — Redis fail-open, Celery, reverse proxy
- [Security](security.md) — redaction and residual limitations
