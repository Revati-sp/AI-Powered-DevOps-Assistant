# Production

Live environment on **Render**. Deploys require manual approval.

## URLs (placeholders)

| Surface | URL |
| --- | --- |
| Frontend | `https://app.example.com` |
| API | `https://api.example.com` |

## Preconditions

Before any production deploy:

1. Staging deploy for the same commit SHA succeeded (smoke tests green).
2. Alembic shows a **single** head; migration reviewed.
3. Database backup status confirmed (Render Postgres backup / PITR as enabled on plan).
4. GitHub Environment `production` reviewers approved the workflow.
5. Image digests recorded from the staging/build job.

## Required secrets

Same categories as staging, with **distinct** values:

- `SECRET_KEY`, `REFRESH_TOKEN_PEPPER`
- Postmark production server token + verified `EMAIL_FROM_ADDRESS`
- Production LLM keys
- OTLP endpoint/headers for the production observability project
- `ALLOWED_ORIGINS`, `FRONTEND_BASE_URL` / `APP_PUBLIC_URL`
- `NEXT_PUBLIC_API_BASE_URL`, optional `AUTH_COOKIE_DOMAIN`
- `METRICS_ALLOWED_IPS` (optional network allowlist)
- Render service IDs + API key in GitHub Environment `production`

`EMAIL_VERIFICATION_REQUIRED=true` is set in the production Blueprint.

## Deployment

Use [`.github/workflows/production-deploy.yml`](../.github/workflows/production-deploy.yml):

- Trigger: `workflow_dispatch` or release tag `v*`
- Requires environment approval
- Deploys immutable image digests when provided
- Runs post-deploy smoke tests

Manual fallback:

```bash
export RENDER_API_KEY=...
export RENDER_SERVICE_ID=<ada-api-production-id>
export IMAGE_URL=ghcr.io/<org>/ai-devops-backend@sha256:<digest>
./deploy/render/scripts/deploy_render.sh
# then worker + frontend with their digests
```

## Migration review

Checklist:

- [ ] `alembic heads` → one revision
- [ ] Migration is expand-only or explicitly reviewed for locks
- [ ] Staging already applied the same revision
- [ ] Rollback plan documented (forward-fix preferred; no auto-downgrade)

API `preDeployCommand` applies `alembic upgrade head` once before new instances go live.

## Post-deploy

```bash
FRONTEND_URL=https://app.example.com \
API_URL=https://api.example.com \
  ./deploy/render/scripts/smoke_test.sh
```

Verify:

- Login / refresh cookie (`Secure`, `HttpOnly`, `SameSite`)
- Email verification path (Postmark activity)
- Worker processes a background task
- `/metrics` denied without auth
- `/docs` returns 404

## Scaling notes

Initial production Blueprint: **2** API and frontend instances, worker concurrency **4**. These are starting points — adjust after load testing. Autoscaling on Render requires a Pro workspace; enable in dashboard if available.

## Known limitations

- Celery Beat is not deployed; periodic cleanup is not scheduled unless invoked externally.
- Redis DB index separation used locally may collapse to one Redis URL in Render (key prefixes still isolate).
- Application rollback does not reverse schema changes.
