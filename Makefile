# Local database and migration helpers.
# Run from the repository root.

COMPOSE_DEV := docker compose -f docker-compose.yml -f docker-compose.dev.yml
DATABASE_URL ?= postgresql+asyncpg://devops:devops@localhost:5432/devops_assistant
MIGRATION_ENV ?= development
APP_ENV ?= development
export DATABASE_URL
export MIGRATION_ENV
export APP_ENV

.PHONY: db-up db-down db-reset db-wait db-migrate db-check db-validate db-upgrade-from-previous

db-up:
	$(COMPOSE_DEV) up -d db

db-down:
	$(COMPOSE_DEV) stop db

db-reset:
	@echo "WARNING: This deletes the local Compose PostgreSQL volume (all local DB data)."
	@echo "Press Ctrl+C within 5 seconds to abort..."
	@sleep 5
	$(COMPOSE_DEV) down -v
	$(COMPOSE_DEV) up -d db
	./scripts/postgres/wait_for_postgres.sh

db-wait:
	./scripts/postgres/wait_for_postgres.sh

db-migrate:
	cd backend && alembic upgrade head

db-check:
	cd backend && alembic check

db-validate:
	./scripts/migrations/validate_local.sh

db-upgrade-from-previous:
	python3 scripts/migrations/upgrade_from_previous.py --database-url "$(DATABASE_URL)"
