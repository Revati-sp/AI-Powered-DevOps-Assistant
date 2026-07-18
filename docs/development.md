# Development

## Prerequisites

- Python 3.12+
- Docker / Docker Compose (optional but recommended)
- PostgreSQL and Redis (or use Compose)

## Setup

```bash
# 1) Start PostgreSQL with the development override (creates devops / devops_assistant)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
./scripts/postgres/wait_for_postgres.sh

# 2) Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit SECRET_KEY and provider API keys
# DATABASE_URL should use localhost when Alembic runs on the host
alembic upgrade head
alembic check
uvicorn app.main:app --reload --port 8000
```

Interactive docs: `http://localhost:8000/docs`

Database details, role-mismatch recovery, and `make db-validate`: [database.md](./database.md).

## Environment

Copy `backend/.env.example` to `.env`. Variables are grouped by concern (app, auth, database, LLM, security, rate limits, Celery, observability). Tests set their own values via `tests/conftest.py` and do not require real LLM keys.

## Quality commands

```bash
cd backend
source .venv/bin/activate

ruff check app tests
ruff format app tests
mypy app
pytest --cov=app --cov-report=term-missing --cov-fail-under=85 -q
python -c "from app.main import app; import json; print(app.title); json.dumps(app.openapi())"
alembic heads
docker compose config
```

## Test layout

| Directory | Purpose |
|---|---|
| `tests/unit/` | Services, RBAC, policy engine, utilities |
| `tests/integration/` | HTTP routes, auth, chat, organizations |
| `tests/security/` | Auth hardening, uploads, SSRF, headers |

Integration tests use in-memory SQLite and mock LLM providers. Rate limiting is disabled in tests.

## Project conventions

- Routes return `APIResponse[T]` envelopes (except OAuth2 login/refresh token responses).
- Paginated lists use `Page` with `items`, `total`, `limit`, `offset` (default limit 20, max 100).
- Sort allowlists use `create_sort_params` / `SortParams`; never accept arbitrary column names.
- Organization permission checks belong in services, not routes.
- Profile email changes are a separate token flow from `PATCH /users/me`.
- Dashboard aggregates live under `/api/v1/dashboard/*` and must not load full chat/artifact payloads.
- Never log secrets, Authorization headers, or full uploaded log content.

## Frontend

The Next.js frontend lives in `frontend/`. See `frontend/.env.example` for API base URL configuration.
