# Database and migrations

## Local defaults (development only)

| Setting | Value |
|---|---|
| User / role | `devops` |
| Password | `devops` |
| Database | `devops_assistant` |
| Host (from laptop / Alembic) | `localhost:5432` |
| Host (from Compose containers) | `db:5432` |
| App / Alembic URL (host) | `postgresql+asyncpg://devops:devops@localhost:5432/devops_assistant` |
| App URL (inside Compose) | `postgresql+asyncpg://devops:devops@db:5432/devops_assistant` |

These credentials are intentionally non-production. Production must set a strong password via secrets / environment — never commit production credentials.

Alembic uses the same async `DATABASE_URL` as the application (`postgresql+asyncpg://...`). There is no separate sync driver requirement.

## Why “role does not exist” happens

PostgreSQL image environment variables (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`) run **only when the data directory is empty** (first container start on a new volume).

If you previously started Postgres with a different user (for example the default `postgres` role), the existing named volume still contains that old cluster. Changing Compose env vars later does **not** recreate the `devops` role.

Typical failure when running Alembic on the host:

```text
asyncpg.exceptions.InvalidAuthorizationSpecificationError: role "devops" does not exist
```

### Fixes

**Option A — reset disposable local volume (destructive)**

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
./scripts/postgres/wait_for_postgres.sh
```

This deletes all data in the local Compose PostgreSQL volume.

**Option B — create the role/database manually** (keeps other local DBs)

```bash
docker exec -it devops-assistant-db psql -U postgres -c "CREATE USER devops WITH PASSWORD 'devops' CREATEDB;"
docker exec -it devops-assistant-db psql -U postgres -c "CREATE DATABASE devops_assistant OWNER devops;"
```

Only works if a superuser role (often `postgres`) still exists in that volume.

## Quick local setup

From the repository root:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
./scripts/postgres/wait_for_postgres.sh
cd backend
cp -n .env.example .env   # if needed
# Ensure DATABASE_URL uses localhost when running Alembic on the host
alembic upgrade head
alembic check
alembic current
alembic heads
```

Backend-only Compose:

```bash
cd backend
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
```

## Full validation

```bash
make db-validate
```

or:

```bash
./scripts/migrations/validate_local.sh
```

This starts Postgres, waits for readiness, verifies the role/database, runs `alembic upgrade head` and `alembic check`.

Safety: scripts require `MIGRATION_ENV` or `APP_ENV` in `{development, test, ci}` unless `--allow-unsafe` is passed.

## Existing-data upgrade smoke test

Creates a temporary database, migrates to the previous revision, inserts a user row, upgrades to head, verifies the row, then drops the temp DB:

```bash
make db-upgrade-from-previous
# or
python3 scripts/migrations/upgrade_from_previous.py
```

## Makefile targets

| Target | Purpose |
|---|---|
| `make db-up` | Start Postgres |
| `make db-down` | Stop Postgres |
| `make db-wait` | Wait until ready |
| `make db-migrate` | `alembic upgrade head` |
| `make db-check` | `alembic check` |
| `make db-validate` | Full local validation |
| `make db-reset` | **Destructive** volume reset + wait |
| `make db-upgrade-from-previous` | Temp DB previous→head data test |

## CI

Backend CI (`.github/workflows/backend-ci.yml`) starts PostgreSQL 16 with the same `devops` / `devops_assistant` credentials, then runs `scripts/migrations/validate.py` and the optional previous→head smoke test.
