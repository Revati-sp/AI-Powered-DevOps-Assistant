#!/usr/bin/env sh
# Wait until PostgreSQL accepts connections.
#
# Environment:
#   POSTGRES_HOST       default: localhost
#   POSTGRES_PORT       default: 5432
#   POSTGRES_USER       default: devops
#   POSTGRES_DB         default: devops_assistant
#   POSTGRES_PASSWORD   optional (not printed)
#   WAIT_TIMEOUT_SECONDS default: 60
#   DATABASE_URL        optional; if set, host/port/user/db are parsed from it
#
# Exit codes:
#   0 — ready
#   1 — timed out or misconfigured

set -eu

TIMEOUT="${WAIT_TIMEOUT_SECONDS:-60}"
HOST="${POSTGRES_HOST:-localhost}"
PORT="${POSTGRES_PORT:-5432}"
USER_NAME="${POSTGRES_USER:-devops}"
DB_NAME="${POSTGRES_DB:-devops_assistant}"

redact_url() {
  # postgresql+driver://user:pass@host:port/db -> postgresql+driver://user:***@host:port/db
  printf '%s\n' "$1" | sed -E 's#(://[^:/@]+:)[^@]+@#\1***@#g'
}

if [ -n "${DATABASE_URL:-}" ]; then
  # Strip driver suffix for parsing: postgresql+asyncpg:// -> postgresql://
  PARSE_URL="$(printf '%s' "$DATABASE_URL" | sed -E 's#^postgresql\+[^:]+://#postgresql://#')"
  # Prefer python for robust URL parsing when available.
  if command -v python3 >/dev/null 2>&1; then
    eval "$(
      DATABASE_URL="$PARSE_URL" python3 - <<'PY'
import os
from urllib.parse import urlparse

url = urlparse(os.environ["DATABASE_URL"])
print(f'HOST="{url.hostname or "localhost"}"')
print(f'PORT="{url.port or 5432}"')
print(f'USER_NAME="{url.username or "devops"}"')
path = (url.path or "/devops_assistant").lstrip("/")
print(f'DB_NAME="{path or "devops_assistant"}"')
PY
    )"
  fi
  echo "Waiting for PostgreSQL at $(redact_url "$DATABASE_URL") (timeout ${TIMEOUT}s)..."
else
  echo "Waiting for PostgreSQL at ${HOST}:${PORT}/${DB_NAME} as ${USER_NAME} (timeout ${TIMEOUT}s)..."
fi

elapsed=0
while [ "$elapsed" -lt "$TIMEOUT" ]; do
  if command -v pg_isready >/dev/null 2>&1; then
    if pg_isready -h "$HOST" -p "$PORT" -U "$USER_NAME" -d "$DB_NAME" >/dev/null 2>&1; then
      echo "PostgreSQL is ready."
      exit 0
    fi
  elif command -v docker >/dev/null 2>&1; then
    # Fallback: use the running compose db container when host tools are missing.
    if docker exec devops-assistant-db pg_isready -U "$USER_NAME" -d "$DB_NAME" >/dev/null 2>&1; then
      echo "PostgreSQL is ready (via docker exec)."
      exit 0
    fi
  elif command -v python3 >/dev/null 2>&1; then
    if DATABASE_URL="${DATABASE_URL:-}" HOST="$HOST" PORT="$PORT" USER_NAME="$USER_NAME" DB_NAME="$DB_NAME" python3 - <<'PY'
import os, socket, sys
host = os.environ["HOST"]
port = int(os.environ["PORT"])
try:
    with socket.create_connection((host, port), timeout=2):
        sys.exit(0)
except OSError:
    sys.exit(1)
PY
    then
      echo "PostgreSQL TCP port is open (pg_isready not installed; install postgresql-client for full checks)."
      exit 0
    fi
  else
    echo "error: need pg_isready, docker, or python3 to wait for PostgreSQL" >&2
    exit 1
  fi

  sleep 1
  elapsed=$((elapsed + 1))
done

echo "error: PostgreSQL not ready within ${TIMEOUT}s" >&2
echo "hint: start with: docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db" >&2
echo "hint: if you see 'role does not exist', the volume may predate POSTGRES_USER=devops — see docs/database.md" >&2
exit 1
