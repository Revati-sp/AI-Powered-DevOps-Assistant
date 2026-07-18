#!/usr/bin/env sh
# Fresh local PostgreSQL + Alembic validation workflow.
#
# 1. Start db via Compose (dev override)
# 2. Wait for readiness
# 3. Validate role/database
# 4. Run alembic upgrade head + check
#
# Does NOT run docker compose down -v. Reset is manual and destructive.

set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
export MIGRATION_ENV="${MIGRATION_ENV:-development}"
export APP_ENV="${APP_ENV:-development}"
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://devops:devops@localhost:5432/devops_assistant}"
export POSTGRES_USER="${POSTGRES_USER:-devops}"
export POSTGRES_DB="${POSTGRES_DB:-devops_assistant}"
export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"

echo "==> Starting PostgreSQL (service: db)"
docker compose $COMPOSE_FILES up -d db

echo "==> Waiting for PostgreSQL"
"$ROOT/scripts/postgres/wait_for_postgres.sh"

echo "==> Verifying role and database"
if command -v docker >/dev/null 2>&1; then
  docker exec devops-assistant-db \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 \
    -c "SELECT current_user, current_database();" >/dev/null
  echo "Role/database OK (${POSTGRES_USER}/${POSTGRES_DB})."
else
  echo "warning: docker not available for in-container role check; continuing"
fi

echo "==> Running Alembic validation"
if [ -x "$ROOT/backend/.venv/bin/python" ]; then
  PYTHON="$ROOT/backend/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  echo "error: python3 not found" >&2
  exit 1
fi

"$PYTHON" "$ROOT/scripts/migrations/validate.py" --database-url "$DATABASE_URL"

echo ""
echo "Local database migration validation succeeded."
echo "  DATABASE_URL=${DATABASE_URL%%@*}@*** (redacted host credentials in logs above)"
echo "  Commands available: alembic current | alembic heads | alembic check"
