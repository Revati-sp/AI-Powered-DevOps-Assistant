# Backend Contract Notes (Frontend Source of Truth)

Inspected: `backend/app` routes, schemas, RBAC, SSE, rate limits, and runtime OpenAPI dump.

## Auth

| Item        | Backend behavior                                                                          | Frontend approach                              |
| ----------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Login       | `POST /api/v1/auth/login` as `application/x-www-form-urlencoded` (`username`, `password`) | BFF route converts form → backend              |
| Tokens      | Bare `TokenPairResponse` (not `APIResponse`)                                              | Parse bare pair on login/refresh               |
| Refresh     | `POST /api/v1/auth/refresh` JSON `{ refresh_token }`                                      | Server-side refresh via HTTP-only cookies      |
| Logout      | JSON `{ refresh_token }`                                                                  | Clear cookies + call backend                   |
| Logout all  | Bearer, no body                                                                           | Proxied with access cookie                     |
| Cookie auth | **Not supported** by FastAPI                                                              | Next.js BFF stores tokens in HTTP-only cookies |

## Envelopes

- Success: `{ success, data, message }`
- Error: `{ success: false, error: { code, message, details } }`
- Exceptions: login/refresh return bare token pair; SSE is raw `text/event-stream`

## RBAC permissions (exact)

`organization.read|update|delete`, `member.manage`, `artifact.read|write`, `policy.read|manage`, `audit.read`, `task.cancel`, `resource.create`

No `artifact.delete`, `task.read`, `conversation.create`, or `analysis.create` enums — map UX to closest permission (`artifact.write`, membership, `resource.create`).

## Profile, dashboard, and lists

1. Profile supports `PATCH /api/v1/users/me` with `username`, `display_name`, `timezone`, `job_title`, and HTTPS `avatar_url`. Email changes use authenticated `POST /api/v1/users/me/email-change/request` with `{ new_email, password }`, followed by unauthenticated `POST /api/v1/users/me/email-change/confirm` with `{ token }`.
2. Dashboard summary, activity, findings, and task aggregates are `GET /api/v1/dashboard/{summary,activity,findings,tasks}` and accept `organization_id` and `time_range` (`24h`, `7d`, `30d`). Summary includes `usage.requests_used` and `usage.requests_limit`.
3. Conversation list is paginated and accepts server-side `search`, `provider`, `organization_id`, `created_from`, `created_to`, `sort_by`, `sort_order`, `limit`, and `offset` filters. Responses use `{ items, total, limit, offset }`; conversation summaries include `organization_id`.
4. Artifact list accepts `search`, `tags`, `favorites_only`, `include_archived`, `archived_only`, `artifact_type`, date, sort, `limit`, and `offset` filters. Responses use `{ items, total, limit, offset }`; artifact URLs synchronize `page`, `search`, `artifact_type`, `tag`, `favorites_only`, `include_archived`, `sort_by`, and `sort_order`.
5. The dashboard UI tolerates individual widget failures via `Promise.allSettled`.

## Remaining gaps

1. Async log analysis cannot attach `organization_id` via public API.
2. Review `type` omits `gitlab-ci` / `jenkins` (policy resource types include them).

## Providers

`gemini` | `llama` | `mistral`

## SSE events

`conversation` → `token`* → `completed` | `error`; ignore `heartbeat`.
