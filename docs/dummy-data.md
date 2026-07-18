# Dummy data

Deterministic sample data for local demos and UI walkthroughs.

**Do not use these accounts or passwords outside local/dev environments.**

## How to seed

Prerequisites: Postgres migrated (`alembic upgrade head`) and API dependencies installed.

From the repo root (API container already running):

```bash
docker compose -f backend/docker-compose.yml -f backend/docker-compose.dev.yml exec api \
  python scripts/seed_dummy_data.py
```

Or from the host with the backend venv and `DATABASE_URL` pointing at local Postgres:

```bash
cd backend
source .venv/bin/activate
python scripts/seed_dummy_data.py
```

Makefile helper:

```bash
make seed-dummy
```

The script is **idempotent**: if `demo.owner@example.com` already exists, it exits without duplicating data.

Source script: [`backend/scripts/seed_dummy_data.py`](../backend/scripts/seed_dummy_data.py)

## Shared password

| Field | Value |
| --- | --- |
| Password (all demo users) | `DummyPass123!` |

## Demo users

| Email | Username | Org role | Notes |
| --- | --- | --- | --- |
| `demo.owner@example.com` | `demo_owner` | **owner** | Full onboarding completed; owns seeded artifacts/chats |
| `demo.admin@example.com` | `demo_admin` | **admin** | Org admin |
| `demo.member@example.com` | `demo_member` | **member** | Partial onboarding; owns a failed sample task |
| `demo.viewer@example.com` | `demo_viewer` | **viewer** | Read-oriented role |
| `demo.personal@example.com` | `demo_personal` | _(none)_ | Personal workspace only (no org membership) |

Suggested login for the richest dashboard: **`demo.owner@example.com` / `DummyPass123!`**

Frontend (local): http://localhost:3001 or http://localhost:3000  
API docs: http://localhost:8000/docs

## Organization

| Field | Value |
| --- | --- |
| Name | Acme Platform |
| Slug | `acme-platform` |
| Members | owner, admin, member, viewer (above) |
| Quota | 100k daily / 2M monthly tokens; 500 daily / 10k monthly requests (`enforce_quotas=false`) |

## Sample content included

| Area | What is seeded |
| --- | --- |
| **Onboarding** | Owner/admin marked complete; member/viewer/personal still have checklist items |
| **Chat** | Org conversation “CrashLoopBackOff triage” with user + assistant messages; personal conversation for `demo_personal` |
| **Artifacts** | `api-service.Dockerfile` (org-scoped) with version 1 |
| **Policies** | Pack “Baseline Security Pack” with two rules (`dockerfile_no_latest`, `ci_no_curl_pipe_bash`) |
| **Log analysis** | Completed log analysis with a high-severity DB connection finding |
| **Reviews** | Completed Dockerfile review with critical/high/medium findings (feeds dashboard) |
| **Tasks** | Succeeded, failed, and queued `analyze_logs` background tasks |
| **Usage** | Several recent Gemini usage events for the owner |
| **Audit** | Org created + policy pack created events |

## Clearing dummy data

Reset the local Compose database volume (destructive — removes **all** local DB data):

```bash
make db-reset
make db-migrate
make seed-dummy
```

## Security notes

- Credentials are intentionally weak and public in this document for local use only.
- Never seed these users into staging or production.
- Never commit real customer data into this seed script.
