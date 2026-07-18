# AI-Powered DevOps Assistant

Backend MVP in [`backend/`](backend/) with a Next.js frontend in [`frontend/`](frontend/).

## Quick start

### Backend

```bash
cd backend
docker compose up --build
```

See [backend/README.md](backend/README.md) for API examples, rate limits, and testing.

### Frontend

```bash
cd frontend && npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Point the app at a running API (`NEXT_PUBLIC_API_BASE_URL` / `INTERNAL_API_BASE_URL`, defaults to `http://localhost:8000`). Full frontend docs: [frontend/README.md](frontend/README.md).

### Full stack (Docker Compose)

From the repo root (includes backend services via `backend/docker-compose.yml` and builds the frontend):

```bash
docker compose up --build
```

| Service | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| Postgres | localhost:5432 |
| Redis | localhost:6379 |

Backend-only Compose still works from `backend/` without the frontend.

### Dummy / demo data

After Postgres is up and migrations have run, load sample users, an organization, chats, artifacts, policies, tasks, and dashboard findings:

```bash
make seed-dummy
```

Full account list, password, and what gets created: **[docs/dummy-data.md](docs/dummy-data.md)**.

Quick login: `demo.owner@example.com` / `DummyPass123!` (local/dev only).

## Deployment

Production target: **Render** (staging + production). See:

- [Deployment](docs/deployment.md)
- [Staging](docs/staging.md)
- [Production](docs/production.md)
- [Email (Postmark SMTP)](docs/email.md)
- [Monitoring](docs/monitoring.md)
- [Rollback](docs/rollback.md)
- [Render blueprints](deploy/render/)

## Documentation

| Doc | Description |
|---|---|
| [Frontend README](frontend/README.md) | Next.js app, BFF auth, env, Docker, tests |
| [Backend README](backend/README.md) | API, workers, local quality checks |
| [Architecture](docs/architecture.md) | Layers, subsystems, API envelopes |
| [Authentication](docs/authentication.md) | JWT, refresh rotation, reuse detection, logout |
| [RBAC](docs/rbac.md) | Organization roles and permission matrix |
| [Security](docs/security.md) | Headers, validation, LLM URL safety |
| [API errors](docs/api-errors.md) | Stable error codes |
| [Operations](docs/operations.md) | Docker, migrations, observability |
| [Development](docs/development.md) | Local setup and quality checks |
| [Dummy data](docs/dummy-data.md) | Local demo users, password, and seeded sample content |
| [Deployment](docs/deployment.md) | Render platform, architecture, secrets |
| [Staging](docs/staging.md) | Staging secrets, smoke tests, reset |
| [Production](docs/production.md) | Production release checklist |
| [Email](docs/email.md) | Postmark / Mailpit configuration |
| [Monitoring](docs/monitoring.md) | Metrics, OTEL, log fields |
| [Rollback](docs/rollback.md) | App rollback and migration limits |

## Security highlights

- JWT access tokens plus server-side refresh token rotation with reuse detection
- Organization RBAC (`owner`, `admin`, `member`, `viewer`)
- Redis rate limiting, upload validation, and security response headers
- Frontend BFF keeps tokens in HTTP-only cookies; browser never holds Bearer secrets
- Generated infrastructure output is preview-only — never executed by the API
