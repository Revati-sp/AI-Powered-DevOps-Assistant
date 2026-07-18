#!/usr/bin/env sh
# Run once per API deploy (Render preDeployCommand). Do not print secrets.
set -eu

echo "Starting database migration (alembic upgrade head)..."
alembic upgrade head
echo "Database migration completed successfully."
