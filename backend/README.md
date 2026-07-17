# AI-Powered DevOps Assistant (Backend)

Production-style MVP backend that helps developers and DevOps engineers ask AI-powered DevOps questions, analyze logs, generate Docker/Kubernetes/CI artifacts, review configuration safely, and retain chat/analysis history.

## Features

- JWT authentication with roles (`user`, `admin`)
- AI chat assistant with conversation history (Gemini provider)
- Log analysis (sync + Celery async)
- Dockerfile, Kubernetes YAML, CI/CD pipeline, and shell command generators
- Configuration security review (static checks + LLM enrichment)
- PostgreSQL persistence, Redis, Celery workers
- Docker Compose local stack
- Structured API responses and centralized error handling

## Architecture

Clean modular layout:

- **Routes** — thin HTTP adapters
- **Services** — business logic
- **Repositories** — database access
- **LLM layer** — provider abstraction (`GeminiProvider` today; Llama/Mistral can be added via factory)
- **Workers** — Celery async tasks

Infrastructure actions are **preview/recommendation only**. The API never executes generated shell commands, applies Kubernetes manifests, runs Docker builds, or applies Terraform.

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
# Set SECRET_KEY and GEMINI_API_KEY in .env
```

### Environment configuration

Key variables (see `.env.example`):

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | JWT signing secret |
| `DATABASE_URL` | Async SQLAlchemy URL (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Redis for readiness checks |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Celery |
| `GEMINI_API_KEY` | Gemini API key |
| `LLM_PROVIDER` | Default provider (`gemini`) |
| `ALLOWED_ORIGINS` | CORS allow-list |
| `MAX_UPLOAD_SIZE_MB` | Upload limit (default 5) |

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

## Running tests

```bash
cd backend
pytest
```

LLM calls are mocked. Real Gemini credentials are not required.

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
- Gemini responses can be incomplete/incorrect — always review before production use

## Future roadmap

- Additional LLM providers (Llama, Mistral)
- Streaming chat responses
- Redis-backed distributed rate limiting
- RBAC for team workspaces
- Persistent artifact versioning UI
- Optional signed policy packs for organization standards
- OpenTelemetry tracing and metrics

## License

Proprietary / internal MVP unless otherwise specified.
