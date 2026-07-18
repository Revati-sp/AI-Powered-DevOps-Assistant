# AI-Powered DevOps Assistant (Backend)

Production-style MVP backend that helps developers and DevOps engineers ask AI-powered DevOps questions, analyze logs, generate Docker/Kubernetes/CI artifacts, review configuration safely, and retain chat/analysis history.

## Features

- JWT authentication with access + refresh tokens (rotation, reuse detection, logout-all)
- Password reset, email verification, and session listing/revocation
- Editable profiles (`PATCH /users/me`) plus separate email-change request/confirm flow
- Password policy validation and bcrypt rehash on login
- Platform roles (`user`, `admin`) plus organization RBAC
- Organization invitations (create, accept, decline, resend, revoke)
- Dashboard aggregate APIs (summary, activity, findings, tasks)
- AI chat assistant with conversation history
- Conversation list search, provider/org/date filters, sorting, and pagination
- Multi-provider LLM support: **Gemini**, **Llama**, **Mistral**
- Provider routing policies (platform + per-org) with circuit-breaker fallbacks
- Usage quotas (organization + optional personal defaults)
- Streaming AI chat via Server-Sent Events (`POST /api/v1/chat/stream`)
- Redis-backed distributed rate limiting
- Log analysis (sync + Celery async)
- Dockerfile, Kubernetes YAML, CI/CD pipeline, and shell command generators
- Configuration security review (static checks + LLM enrichment)
- Artifact tags, favorites, archive, type/date filters, and sorting
- User onboarding progress tracking
- PostgreSQL persistence, Redis, Celery workers
- Docker Compose local stack
- Structured API responses and centralized error handling
- Organizations, RBAC, artifact versioning, policy packs, and audit logging
- Persistent background tasks with cancellation and idempotency
- Optional OpenTelemetry tracing and Prometheus metrics
- GitHub Actions CI for lint, type-check, tests, migrations, and Docker build

## Architecture

Clean modular layout (see [../docs/architecture.md](../docs/architecture.md)):

- **Routes** — thin HTTP adapters
- **Services** — business logic
- **Repositories** — database access
- **LLM layer** — provider abstraction (`GeminiProvider`, `LlamaProvider`, `MistralProvider`)
- **Rate limiting** — atomic Redis sliding-window limiter
- **Workers** — Celery async tasks

Infrastructure actions are **preview/recommendation only**. The API never executes generated shell commands, applies Kubernetes manifests, runs Docker builds, or applies Terraform.

## Documentation

| Doc | Description |
|---|---|
| [Architecture](../docs/architecture.md) | Layers, subsystems, envelopes |
| [Authentication](../docs/authentication.md) | Refresh rotation, reuse detection, logout |
| [RBAC](../docs/rbac.md) | Role permission matrix |
| [Security](../docs/security.md) | Headers, uploads, LLM URL validation |
| [API errors](../docs/api-errors.md) | Error codes from `app/core/error_codes.py` |
| [Operations](../docs/operations.md) | Docker, migrations, metrics |
| [Development](../docs/development.md) | Local setup and test commands |

## Project structure

```text
backend/
├── app/
│   ├── api/routes/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── workers/
│   └── utils/
├── alembic/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── requirements.txt
```

## Local setup

### Prerequisites

- Python 3.12+
- Docker / Docker Compose (recommended)
- PostgreSQL + Redis (if not using Compose)

### Install

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set SECRET_KEY and provider API keys in .env
```

### Environment configuration

Key variables (see `.env.example`):

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | JWT signing secret |
| `DATABASE_URL` | Async SQLAlchemy URL (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Redis for readiness checks and rate limiting |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Celery |
| `LLM_PROVIDER` | Default provider (`gemini`, `llama`, or `mistral`) |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Gemini configuration |
| `LLAMA_API_KEY` / `LLAMA_BASE_URL` / `LLAMA_MODEL` | Llama (OpenAI-compatible) |
| `MISTRAL_API_KEY` / `MISTRAL_BASE_URL` / `MISTRAL_MODEL` | Mistral (OpenAI-compatible) |
| `LLM_REQUEST_TIMEOUT_SECONDS` / `LLM_MAX_RETRIES` | Shared LLM HTTP settings |
| `ALLOW_INSECURE_LLM_HTTP` | Allow `http://` provider URLs (dev only; default `false`) |
| `SSE_HEARTBEAT_INTERVAL_SECONDS` | Streaming heartbeat interval |
| `RATE_LIMIT_*` | Distributed rate-limit configuration |
| `TRUSTED_PROXY_COUNT` | How many reverse proxies to trust for client IP |
| `ALLOWED_ORIGINS` | CORS allow-list |
| `MAX_UPLOAD_SIZE_MB` | Upload limit (default 5) |
| `CELERY_TASK_*` / `BACKGROUND_TASK_RETENTION_DAYS` | Celery limits and task retention |
| `OTEL_*` | Optional OpenTelemetry tracing |
| `METRICS_*` | Prometheus `/metrics` endpoint controls |
| `EMAIL_ENABLED` | Enable outbound email (SMTP or capture in tests) |
| `EMAIL_VERIFICATION_REQUIRED` | Block login until email is verified |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` | SMTP credentials |
| `SMTP_FROM_EMAIL` / `SMTP_USE_TLS` | From address and TLS |
| `PASSWORD_RESET_TOKEN_MINUTES` | Password reset link lifetime |
| `EMAIL_VERIFICATION_TOKEN_MINUTES` | Email verification link lifetime |
| `INVITATION_EXPIRE_HOURS` | Organization invitation lifetime |
| `FRONTEND_BASE_URL` | Base URL for email deep links |
| `USAGE_ENFORCE_PERSONAL_QUOTAS` | Enforce personal token limits when no org is set |
| `USAGE_DEFAULT_DAILY_TOKEN_LIMIT` / `USAGE_DEFAULT_MONTHLY_TOKEN_LIMIT` | Personal quota defaults |

### Email / SMTP

Set `EMAIL_ENABLED=true` and configure `SMTP_*` for real delivery. With `EMAIL_ENABLED=false`, the app still records verification/reset/invite intent but does not send mail. When `EMAIL_VERIFICATION_REQUIRED=true`, registration automatically sends a verification email and login is rejected until the user verifies.

## Authentication and security

Access tokens authorize API requests. Refresh tokens rotate on each `POST /api/v1/auth/refresh`; reuse of a spent token revokes the entire token family. Logout endpoints revoke refresh tokens server-side.

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/auth/register` | Create account |
| `POST /api/v1/auth/login` | OAuth2 password flow → token pair |
| `POST /api/v1/auth/refresh` | Rotate refresh token |
| `POST /api/v1/auth/logout` | Revoke one refresh token |
| `POST /api/v1/auth/logout-all` | Revoke all sessions (requires access token) |
| `POST /api/v1/auth/forgot-password` | Request password reset email |
| `POST /api/v1/auth/reset-password` | Complete password reset with token |
| `POST /api/v1/auth/change-password` | Change password (authenticated) |
| `POST /api/v1/auth/send-verification` | Resend email verification |
| `POST /api/v1/auth/verify-email` | Verify email with token |
| `GET /api/v1/auth/sessions` | List active refresh sessions |
| `DELETE /api/v1/auth/sessions/{id}` | Revoke a specific session |

See [../docs/authentication.md](../docs/authentication.md) and [../docs/security.md](../docs/security.md).

Configure `SECRET_KEY`, `REFRESH_TOKEN_PEPPER`, and JWT settings in `.env.example` (Auth section).

## Profiles and email change

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/users/me` | Safe user profile (includes `display_name`, `timezone`, `job_title`, `avatar_url`) |
| `PATCH /api/v1/users/me` | Update username / display name / timezone / job title / avatar URL |
| `POST /api/v1/users/me/email-change/request` | Password-gated request; generic response |
| `POST /api/v1/users/me/email-change/confirm` | One-time token confirm (unauthenticated); revokes all refresh sessions |

Profile PATCH rejects role, email, password, and other security fields (`extra=forbid`). Username changes are uniqueness-checked and reserved-name blocked. Meaningful profile updates emit `user.profile.updated` audit events.

## Dashboard aggregates

Use these instead of stitching large list queries on the client:

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/dashboard/summary` | Counts for conversations, artifacts, tasks, findings, usage, org |
| `GET /api/v1/dashboard/activity` | Unified recent activity feed |
| `GET /api/v1/dashboard/findings` | Severity counts (+ recent finding summaries) |
| `GET /api/v1/dashboard/tasks` | Task status counts (+ recent task summaries) |

Query params: optional `organization_id`, `time_range` (`24h` \| `7d` \| `30d`, default `7d`). Personal scope (no org) returns only the caller's data. Org scope enforces membership/RBAC. Findings are derived from persisted review `Analysis.result_json`.

## Conversation list filters

`GET /api/v1/chat/conversations` returns `Page[ConversationSummary]` (`items`, `total`, `limit`, `offset`).

Filters/sort: `search` (title), `provider`, `organization_id`, `created_from`, `created_to`, `sort_by` (`created_at` \| `updated_at` \| `title`), `sort_order`, `limit` (default 20, max 100), `offset`. Summaries include `organization_id` and never embed message history.

## Organizations and RBAC

Organizations are team workspaces with roles (`owner`, `admin`, `member`, `viewer`). Personal resources keep `organization_id = null`.

Key routes:

- `POST/GET/PATCH/DELETE /api/v1/organizations`
- `GET/POST/PATCH/DELETE /api/v1/organizations/{id}/members`

Authorization is centralized in `OrganizationAuthService` with permission enums such as `artifact.read`, `policy.manage`, and `task.cancel`. Full matrix: [../docs/rbac.md](../docs/rbac.md).

## Artifacts and versioning

Generated artifacts support version history, unified diffs, and restore-as-new-version behavior.

- `POST/GET/PATCH/DELETE /api/v1/artifacts`
- `GET/POST /api/v1/artifacts/{id}/versions`
- `POST /api/v1/artifacts/{id}/versions/{n}/restore`
- `GET /api/v1/artifacts/{id}/diff`

List filters: `search`, `tags`, `favorites_only`, `include_archived`, `archived_only`, `creator_id`, `artifact_type`, `organization_id`, `created_from`/`created_to`, `updated_from`/`updated_to`, `sort_by` (`created_at` \| `updated_at` \| `name` \| `artifact_type` \| `current_version_number`), `sort_order`, `limit`, `offset`. Default list excludes archived artifacts. List responses omit full content.

Generators accept optional `save_artifact`, `artifact_name`, and `organization_id` fields.

## Policy packs

Organization-scoped deterministic policy packs validate reviews and optional generator output.

- Policy pack CRUD under `/api/v1/organizations/{id}/policy-packs`
- Review responses include `built_in_findings`, `organization_policy_findings`, and `llm_findings`

## Audit logging

Append-only audit events capture security-sensitive actions with recursive metadata redaction.

- `GET /api/v1/organizations/{id}/audit-events` (owner/admin)

## Background tasks

Persistent background tasks track async work such as log analysis.

- `GET /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `POST /api/v1/tasks/{task_id}/cancel`
- `POST /api/v1/logs/analyze/async` supports `Idempotency-Key`

Task responses use the persistent task UUID as the primary `task_id`. Compatibility fields include `analysis_id` and `celery_task_id`.

## Observability

Optional OpenTelemetry tracing is controlled by `OTEL_ENABLED`. When disabled, no exporter is required.

Prometheus metrics are exposed at `GET /metrics` when `METRICS_ENABLED=true`. Health and readiness endpoints are not rate-limited.

Every response includes `X-Request-ID`.

## CI

GitHub Actions workflow: `.github/workflows/backend-ci.yml`

Checks:

- Ruff lint and format
- MyPy
- Pytest with `--cov-fail-under=85`
- Alembic upgrade/check against PostgreSQL
- Application import and OpenAPI dump
- Docker Compose config and Docker build
- `pip-audit` and optional `gitleaks`

Local equivalents:

```bash
cd backend
ruff check app tests
ruff format --check app tests
mypy app
pytest --cov=app --cov-report=term-missing --cov-fail-under=85
alembic upgrade head
alembic check
python -c "from app.main import app; print(app.title)"
python -c "from app.main import app; import json; json.dumps(app.openapi())"
docker compose config
docker build .
```

Provider calls and telemetry exporters are mocked in tests; real credentials are not required.

### Database migrations

```bash
alembic upgrade head
```

### Run API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Celery worker

```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

## Docker setup

```bash
cd backend
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Celery worker

Docs: `http://localhost:8000/docs`

## LLM providers

Supported provider names (case-insensitive):

- `gemini`
- `llama`
- `mistral`

Select per request with `"provider": "llama"` or set `LLM_PROVIDER` as the default.

Llama and Mistral use OpenAI-compatible HTTP APIs:

```text
POST {BASE_URL}/chat/completions
Authorization: Bearer <API_KEY>
```

Provider base URLs must be `https` by default. Set `ALLOW_INSECURE_LLM_HTTP=true` only for local development. URLs with embedded credentials are rejected.

All provider unit/integration tests mock HTTP. Real credentials are not required for `pytest`.

## Streaming chat (SSE)

Endpoint:

```text
POST /api/v1/chat/stream
Content-Type: application/json
Accept: text/event-stream
```

SSE event types:

| Event | Meaning |
|---|---|
| `conversation` | Conversation ID (always first) |
| `token` | Incremental assistant text chunk |
| `heartbeat` | Keep-alive during long pauses |
| `completed` | Stream finished; assistant message persisted |
| `error` | Stream failed after it started |

Example:

```bash
curl -N \
  -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain CrashLoopBackOff",
    "provider": "llama"
  }'
```

Persistence rules:

- User message is saved before generation starts
- Assistant message is saved only after successful completion
- Failed/cancelled streams do not persist an assistant message

The non-streaming `POST /api/v1/chat` endpoint remains unchanged.

## Rate limiting

Distributed sliding-window limits are stored in Redis (atomic Lua). Defaults:

| Category | Default | Identity |
|---|---|---|
| Auth (`/auth/login`, `/auth/register`) | 10/min | Client IP |
| API (protected non-LLM routes) | 120/min | User ID |
| LLM (chat, generators, review) | 20/min | User ID |
| Stream (`/chat/stream`) | 10/min | User ID |
| Upload / log analysis | 10/min | User ID |
| Health / ready / metrics | Unlimited | — |

Exceeded requests return HTTP `429` with:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Try again later.",
    "details": {"retry_after_seconds": 42}
  }
}
```

Headers:

- `Retry-After`
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

Redis failure behavior:

- `RATE_LIMIT_FAIL_OPEN=true` (default): allow the request and log a warning
- `RATE_LIMIT_FAIL_OPEN=false`: return HTTP `503`

Streaming limits are checked **before** SSE starts, conversation creation, persistence, or LLM calls.

Forwarded IP headers are ignored unless `TRUSTED_PROXY_COUNT > 0`.

## Running tests

```bash
cd backend
pytest
```

LLM calls and provider HTTP are mocked. Real Gemini/Llama/Mistral credentials are not required.

Quality checks:

```bash
ruff check app tests
ruff format --check app tests
mypy app
```

## API examples

### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"dev@example.com","username":"devops","password":"securepass123"}'
```

### Login (OAuth2 password flow)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d 'username=devops&password=securepass123'
```

### Password reset / email verification

```bash
curl -X POST http://localhost:8000/api/v1/auth/forgot-password \
  -H 'Content-Type: application/json' \
  -d '{"email":"dev@example.com"}'

curl -X POST http://localhost:8000/api/v1/auth/reset-password \
  -H 'Content-Type: application/json' \
  -d '{"token":"<reset-token>","new_password":"NewSecurePass123!"}'

curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H 'Content-Type: application/json' \
  -d '{"token":"<verification-token>"}'
```

### Sessions

```bash
curl http://localhost:8000/api/v1/auth/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Refresh-Token: $REFRESH_TOKEN"
```

### Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"message":"Why is my Kubernetes pod in CrashLoopBackOff?","conversation_id":null,"provider":"gemini"}'
```

### Analyze logs

```bash
curl -X POST http://localhost:8000/api/v1/logs/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"content":"CrashLoopBackOff\nERROR: Job failed","provider":"gemini"}'
```

Upload a `.log` / `.txt` file (max 5 MB):

```bash
curl -X POST http://localhost:8000/api/v1/logs/analyze/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F 'file=@./app.log' \
  -F 'provider=gemini'
```

### Generate Dockerfile

```bash
curl -X POST http://localhost:8000/api/v1/generate/dockerfile \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"language":"python","framework":"fastapi","python_version":"3.12","port":8000,"use_multistage":true,"run_as_non_root":true}'
```

### Health

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## Security limitations (MVP)

- Generated commands/artifacts are suggestions only and are **never executed**
- No automatic cluster, Docker daemon, or Terraform mutations
- File uploads are size/type validated, but treat all AI output as untrusted
- Set a strong `SECRET_KEY` and never commit real `.env` values
- Never log API keys, Authorization headers, full prompts, or uploaded logs
- AI responses can be incomplete/incorrect — always review before production use

## Future roadmap

- Live LLM health probes beyond circuit-breaker snapshots
- Shared organization-wide artifact tags (cross-user tag catalogs)
- Richer personal quota dashboards and admin overrides

## License

Proprietary / internal MVP unless otherwise specified.
