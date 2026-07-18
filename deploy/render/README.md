# Render deployment

Single production deployment target for the AI-Powered DevOps Assistant.

## Architecture

| Component | Render resource | Image / runtime |
| --- | --- | --- |
| Frontend | Web service | `frontend/Dockerfile` |
| API | Web service | `backend/Dockerfile` |
| Celery worker | Background worker | same backend image |
| PostgreSQL | Managed Postgres | separate staging / production |
| Redis | Managed Key Value | separate staging / production |
| Migrations | API `preDeployCommand` | `alembic upgrade head` once per API deploy |

HTTPS, custom domains, and TLS termination are provided by Render. HTTP redirects to HTTPS automatically on custom domains.

Celery Beat is **not** deployed (no scheduler is required by the current worker tasks).

## Blueprint files

| Environment | File |
| --- | --- |
| Staging | [`render.staging.yaml`](./render.staging.yaml) |
| Production | [`render.production.yaml`](./render.production.yaml) |

Create **two** Render Blueprints (or two projects), each pointing at the matching file. Do not share databases, Redis instances, or secrets between staging and production.

## First-time setup

1. Connect the GitHub repository to Render.
2. Create Blueprint from `deploy/render/render.staging.yaml`.
3. Fill all `sync: false` secrets in the dashboard (see [docs/staging.md](../../docs/staging.md)).
4. Attach custom domains (placeholders in docs).
5. Repeat for production with `render.production.yaml` and stronger plans / approvals.
6. Configure GitHub Environments `staging` and `production` with Render service IDs and API key (or deploy hooks).

## Migration strategy

- Only the **API** service runs `preDeployCommand: sh scripts/deploy_migrate.sh`.
- Workers and frontend do **not** run Alembic.
- Migration failure blocks the API deploy (Render fails the release).
- Application rollback does **not** automatically downgrade the database.

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/validate_blueprint.sh` | Structural YAML checks |
| `scripts/smoke_test.sh` | Post-deploy HTTPS health/ready checks |
| `scripts/deploy_render.sh` | Trigger Render deploy via API (optional image digest) |
| `backend/scripts/deploy_migrate.sh` | Safe `alembic upgrade head` |

## Documentation

- [Deployment](../../docs/deployment.md)
- [Staging](../../docs/staging.md)
- [Production](../../docs/production.md)
- [Email](../../docs/email.md)
- [Rollback](../../docs/rollback.md)
- [Monitoring](../../docs/monitoring.md)
