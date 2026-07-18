# Rollback

## Application rollback

Prefer redeploying a previous **immutable image digest** (or known-good commit) for:

1. API
2. Worker (same backend digest as API)
3. Frontend

Via Render dashboard → service → **Rollback**, or:

```bash
export RENDER_API_KEY=...
export RENDER_SERVICE_ID=<service-id>
export IMAGE_URL=ghcr.io/<org>/<image>@sha256:<previous-digest>
./deploy/render/scripts/deploy_render.sh
```

Keep API and worker on the **same** application version.

## Database rollback limitations

- Deploys run **`alembic upgrade head` only**.
- **Do not** automatically `alembic downgrade` when rolling back the application.
- Schema changes are forward-only unless an explicitly reviewed downgrade is run by an operator.
- If a migration is incompatible with the previous app version, roll forward with a fix migration instead of downgrading when possible.

## When a migration already applied

1. Leave the database at the new revision.
2. Deploy an application build that is compatible with that schema (roll forward).
3. Only if necessary, run a manual downgrade from a break-glass shell after backup restore planning — never from CI automatically.

## Staging reset

Staging may wipe data and re-run `upgrade head`. Production must not.

## Verification after rollback

```bash
FRONTEND_URL=... API_URL=... ./deploy/render/scripts/smoke_test.sh
```

Confirm auth, readiness, and that workers consume tasks.
