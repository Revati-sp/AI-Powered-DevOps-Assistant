# Staging

Production-like environment on **Render**. Never use production data.

## URLs (placeholders)

| Surface | URL |
| --- | --- |
| Frontend | `https://app.staging.example.com` |
| API | `https://api.staging.example.com` |

Replace after attaching custom domains in the Render dashboard.

## Required secrets

Set on Render services / env group (and mirror IDs in GitHub Environment `staging`):

| Secret | Where |
| --- | --- |
| `SECRET_KEY` | API + worker (≥32 chars, unique to staging) |
| `REFRESH_TOKEN_PEPPER` | API + worker |
| `ALLOWED_ORIGINS` | API (`https://app.staging.example.com`) |
| `FRONTEND_BASE_URL` / `APP_PUBLIC_URL` | API |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend |
| `AUTH_COOKIE_DOMAIN` | Frontend (optional) |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | API (Postmark Server Token) |
| `EMAIL_FROM_ADDRESS` / `SMTP_FROM_EMAIL` | API (verified sender) |
| `GEMINI_API_KEY` (or other LLM) | API + worker — prefer low-cost / mock keys |
| `OTEL_EXPORTER_OTLP_ENDPOINT` / `HEADERS` | API + worker |
| `RENDER_API_KEY` | GitHub Environment `staging` |
| `RENDER_API_SERVICE_ID` | GitHub |
| `RENDER_WORKER_SERVICE_ID` | GitHub |
| `RENDER_FRONTEND_SERVICE_ID` | GitHub |
| `STAGING_FRONTEND_URL` / `STAGING_API_URL` | GitHub (smoke tests) |

Managed `DATABASE_URL` and Redis URLs are injected by the Blueprint (`fromDatabase` / `fromService`).

## Deployment command

Blueprint sync (first create / infra changes):

1. Open Render → Blueprints → apply [`deploy/render/render.staging.yaml`](../deploy/render/render.staging.yaml).
2. Fill `sync: false` values when prompted.

Application deploy (ongoing):

```bash
# Via GitHub Actions (push to main touching app paths, or workflow_dispatch)
# Or manually:
export RENDER_API_KEY=...
export RENDER_SERVICE_ID=<ada-api-staging-id>
./deploy/render/scripts/deploy_render.sh
```

Recommended order in CI: migrate+API (preDeploy runs migrate) → worker → frontend → smoke tests.

## Migration command

Runs automatically on API deploy:

```bash
sh scripts/deploy_migrate.sh   # inside API image → alembic upgrade head
```

Manual (from a one-off shell with staging `DATABASE_URL`, never log the URL):

```bash
cd backend
alembic upgrade head
alembic current
```

## Smoke-test command

```bash
FRONTEND_URL=https://app.staging.example.com \
API_URL=https://api.staging.example.com \
  ./deploy/render/scripts/smoke_test.sh
```

## Test email behavior

- Provider: **Postmark** over SMTP (`smtp.postmarkapp.com`).
- Use a Postmark **Server** dedicated to staging (or Message Stream tagged staging).
- `EMAIL_LOG_BODIES=false` — never log one-time links.
- Console provider is rejected when `APP_ENV=staging`.

## LLM configuration

Prefer:

- Cheap/flash models
- Strict rate limits
- Separate API keys from production
- Optional lower quotas via usage settings

Do not point staging at production provider projects if billing isolation matters.

## Reset procedure

Destructive — staging only:

1. Drop/recreate Render Postgres **or** `alembic downgrade` is **not** recommended; prefer fresh DB + `upgrade head`.
2. Flush Redis Key Value (or recreate instance).
3. Redeploy API (runs migrations) + worker + frontend.
4. Re-seed test users manually if needed.

Never restore a production backup into staging without explicit redaction and approval.

## Rollback procedure

See [rollback.md](./rollback.md). Staging can redeploy the previous image digest / commit via Render dashboard or `deploy_render.sh` with a prior digest.

## Security posture

Staging mirrors production security:

- HTTPS only, HSTS on
- Secure auth cookies
- Docs/OpenAPI off
- Metrics require auth
- Trusted proxy count = 1
- Separate CORS allowlist
