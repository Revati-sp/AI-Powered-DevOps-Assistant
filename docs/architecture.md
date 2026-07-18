# Architecture

The backend is a FastAPI application organized in layers. HTTP adapters stay thin; business rules live in services; SQLAlchemy access is isolated in repositories.

## Layers

| Layer | Location | Responsibility |
|---|---|---|
| Routes | `backend/app/api/routes/` | HTTP validation, auth dependencies, rate limits, response envelopes |
| Services | `backend/app/services/` | Business logic, orchestration, RBAC checks |
| Repositories | `backend/app/repositories/` | Database queries and persistence |
| Models | `backend/app/models/` | SQLAlchemy ORM entities |
| Schemas | `backend/app/schemas/` | Pydantic request/response models |
| Workers | `backend/app/workers/` | Celery tasks for async work |

## Request flow

```text
Client → Middleware (request ID, size limits, security headers, CORS)
      → Route handler
      → Service
      → Repository / external provider (LLM, Redis)
      → APIResponse envelope or structured ErrorResponse
```

## Major subsystems

- **Authentication** — JWT access tokens plus server-side refresh token rotation (`AuthService`, `RefreshTokenRepository`).
- **User profiles** — Editable profile fields via `PATCH /users/me`; email changes use a separate request/confirm token flow (`ProfileService`).
- **Organizations & RBAC** — Multi-tenant workspaces with role-based permissions (`OrganizationAuthService`).
- **Dashboard** — Aggregate summary, activity, findings, and task endpoints scoped by personal/org context and time range (`DashboardService`).
- **Chat** — Sync and SSE streaming chat with conversation history (`ChatService`, LLM provider factory); conversation lists support search, filters, sorting, and pagination.
- **Generators & reviews** — Dockerfile, Kubernetes, CI, shell command generation; static + policy + LLM security review.
- **Artifacts** — Versioned generated content with diff and restore; list APIs support search, tags, favorites, archive, type, dates, and sorting.
- **Policy engine** — Organization policy packs evaluated deterministically.
- **Audit** — Append-only security event log with metadata redaction.
- **Background tasks** — Persistent task records backed by Celery for async log analysis and similar work.
- **Rate limiting** — Redis sliding-window limiter with per-route categories.
- **Observability** — Optional OpenTelemetry tracing and Prometheus metrics.

## API envelope

Successful responses use:

```json
{"success": true, "data": {}, "message": null}
```

Errors use:

```json
{"success": false, "error": {"code": "NOT_FOUND", "message": "...", "details": {}}}
```

Paginated list endpoints return `data` as a `Page` object: `{items, total, limit, offset}`.

Default page size is 20 (maximum 100). Sort fields are allowlisted per resource via `create_sort_params` (for example conversations: `created_at`, `updated_at`, `title`; artifacts: `created_at`, `updated_at`, `name`, `artifact_type`, `current_version_number`). Stable secondary ordering uses the primary key.

## Infrastructure boundary

The API never executes generated shell commands, applies Kubernetes manifests, runs Docker builds, or mutates external infrastructure. Outputs are preview/recommendation only.

## Related docs

- [Authentication](authentication.md)
- [RBAC](rbac.md)
- [Security](security.md)
- [Operations](operations.md)
- [API errors](api-errors.md)
- [Development](development.md)
