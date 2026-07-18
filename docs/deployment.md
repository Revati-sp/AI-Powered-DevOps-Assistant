# Deployment

## Selected platform

**Render** is the sole production deployment target.

Why Render fits this stack:

- Docker web services for Next.js and FastAPI
- Background workers for Celery (same backend image)
- Managed PostgreSQL and Redis (Key Value)
- `preDeployCommand` for a single migration job per API deploy
- HTTPS + custom domains + HTTP→HTTPS redirects
- Dashboard secret / environment management
- Health checks (`healthCheckPath`)
- GitHub Actions can trigger deploys via the Render API

Blueprint files live under [`deploy/render/`](../deploy/render/).

## Architecture

```text
Internet (HTTPS)
    │
    ├─ Frontend (Next.js) ── BFF ── INTERNAL_API_BASE_URL ──► API (private)
    │                              PUBLIC API URL (browser) ──► API (HTTPS)
    │
    ├─ API (FastAPI) ── PostgreSQL (managed)
    │                └─ Redis (managed) — rate limits, cache, Celery
    │
    └─ Celery worker (same backend image) ── PostgreSQL + Redis
```

| Service | Staging name | Production name | Initial sizing (sensible defaults, not universally optimal) |
| --- | --- | --- | --- |
| Frontend | `ada-frontend-staging` | `ada-frontend-production` | Staging: 1× starter; Prod: 2× standard |
| API | `ada-api-staging` | `ada-api-production` | Staging: 1× starter; Prod: 2× standard |
| Worker | `ada-worker-staging` | `ada-worker-production` | Staging: concurrency 2; Prod: concurrency 4 |
| Postgres | `ada-postgres-staging` | `ada-postgres-production` | Separate instances; never share data |
| Redis | `ada-redis-staging` | `ada-redis-production` | Private network only (`ipAllowList: []`) |

### Resource knobs (application)

| Setting | Staging | Production | Notes |
| --- | --- | --- | --- |
| API replicas | 1 | 2 | Scale with traffic; watch DB pool |
| Worker concurrency | 2 | 4 | Celery `--concurrency` |
| Celery soft / hard limits | 540s / 600s | same | `CELERY_TASK_*` |
| DB pool | SQLAlchemy defaults | tune if replicas grow | Avoid oversubscribing managed Postgres |
| Redis | one Key Value instance | separate instance | Broker + app share URL; key prefixes isolate |
| Max SSE connections | app/process limited | monitor memory | No hard global cap in MVP |

## Environments

| Name | Purpose |
| --- | --- |
| `development` | Local Docker / Mailpit / console email |
| `test` | CI / pytest |
| `staging` | Production-like HTTPS preview |
| `production` | Live users |

Staging and production each have separate databases, Redis, secrets, domains, CORS, email credentials, LLM keys, and quotas.

## Containers

- Backend: multi-stage image, non-root `app`, healthcheck on `/health`, graceful uvicorn shutdown, no `.env` in image (see `backend/.dockerignore`).
- Frontend: multi-stage standalone Next.js, non-root `nextjs`, healthcheck on `/`.
- Worker uses the **same** backend image with a different `dockerCommand`.

## Migrations

1. API deploy starts.
2. Render runs `preDeployCommand` → `sh scripts/deploy_migrate.sh` → `alembic upgrade head`.
3. On success, new API instances receive traffic.
4. On failure, deploy stops; previous API revision remains.

Confirm a single Alembic head before release (`alembic heads`). See [rollback.md](./rollback.md) for limitations.

## Domains and HTTPS

| Surface | Staging placeholder | Production placeholder |
| --- | --- | --- |
| Frontend | `https://app.staging.example.com` | `https://app.example.com` |
| API | `https://api.staging.example.com` | `https://api.example.com` |

Configure on Render:

- Custom domains + managed certificates
- `ALLOWED_ORIGINS` = frontend origin(s) only
- `FRONTEND_BASE_URL` / `APP_PUBLIC_URL` = public frontend HTTPS URL
- `NEXT_PUBLIC_API_BASE_URL` = public API HTTPS URL
- `INTERNAL_API_BASE_URL` = private `http://<api-service>:8000`
- `AUTH_COOKIE_SECURE=true`, `SameSite=lax` (or `strict` if applicable)
- `TRUSTED_PROXY_COUNT=1` (Render edge)
- `HSTS_ENABLED=true`
- Docs/OpenAPI disabled; metrics auth required

## Secrets

Store only in Render env groups / dashboard and GitHub Environment secrets. Never in git, images, or `NEXT_PUBLIC_*`.

Minimum API secrets: `SECRET_KEY`, `REFRESH_TOKEN_PEPPER`, SMTP credentials, LLM keys, OTLP headers, CORS/public URLs.

## Deploy workflows

- Staging: [`.github/workflows/staging-deploy.yml`](../.github/workflows/staging-deploy.yml)
- Production: [`.github/workflows/production-deploy.yml`](../.github/workflows/production-deploy.yml)

## Related docs

- [Staging](./staging.md)
- [Production](./production.md)
- [Email](./email.md)
- [Monitoring](./monitoring.md)
- [Rollback](./rollback.md)
- [Operations](./operations.md)
