# Operations

## Docker Compose (local)

```bash
cd backend
docker compose up --build
```

Services:

| Service | Port | Purpose |
|---|---|---|
| `api` | 8000 | FastAPI app (runs migrations on start) |
| `worker` | — | Celery worker |
| `db` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Rate limiting and Celery broker |

The API container runs as non-root user `app` (uid 1000). Health check: `GET /health`.

## Database migrations

PostgreSQL must be running with the `devops` role and `devops_assistant` database. Prefer:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
./scripts/postgres/wait_for_postgres.sh
cd backend
alembic upgrade head
alembic check          # compare models to DB (requires PostgreSQL)
alembic heads          # should show a single head
alembic current
```

Full local validation: `make db-validate` (see [database.md](./database.md)).

`POSTGRES_USER` / `POSTGRES_DB` only initialize a **new** empty volume. An existing volume with a different role causes `role "devops" does not exist` — reset with `docker compose ... down -v` (destructive) or create the role manually.

Migration revisions live under `backend/alembic/versions/` (`001` … current head).

## Health and readiness

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness |
| `GET /ready` | Checks database and Redis connectivity |
| `GET /metrics` | Prometheus metrics when `METRICS_ENABLED=true` |

These endpoints are not rate-limited.

## Observability

- **Request tracing** — Every response includes `X-Request-ID`.
- **OpenTelemetry** — Enable with `OTEL_ENABLED=true` and configure OTLP endpoint/headers.
- **Prometheus** — HTTP request and rate-limit rejection metrics when metrics are enabled.

## Background workers

```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

Task retention is controlled by `BACKGROUND_TASK_RETENTION_DAYS`. Celery time limits via `CELERY_TASK_*` settings.

## CI checks

GitHub Actions (`.github/workflows/backend-ci.yml`) runs lint, type-check, tests (85% coverage floor), migrations, OpenAPI import, Docker build, and `pip-audit`.

## Production checklist

- Set `APP_ENV=production`, strong `SECRET_KEY` and `REFRESH_TOKEN_PEPPER` (≥32 chars).
- Configure `ALLOWED_ORIGINS` explicitly (no wildcard).
- Keep `ALLOW_INSECURE_LLM_HTTP=false`.
- Enable HSTS via production defaults.
- Restrict metrics endpoint (`METRICS_REQUIRE_AUTH` / `METRICS_ALLOWED_IPS`) if exposed.
