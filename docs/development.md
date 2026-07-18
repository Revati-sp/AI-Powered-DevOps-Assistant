# Development

## Prerequisites

- Python 3.12+
- Docker / Docker Compose (optional but recommended)
- PostgreSQL and Redis (or use Compose)

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit SECRET_KEY and provider API keys
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Interactive docs: `http://localhost:8000/docs`

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
- Paginated lists use `Page` with `items`, `total`, `limit`, `offset`.
- Organization permission checks belong in services, not routes.
- Never log secrets, Authorization headers, or full uploaded log content.

## Frontend

The Next.js frontend lives in `frontend/`. See `frontend/.env.example` for API base URL configuration.
