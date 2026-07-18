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

## Documented gaps (no backend change)

1. Profile is read-only (`GET /users/me` only).
2. Conversation list is unpaginated; DTOs omit `organization_id`.
3. Async log analysis cannot attach `organization_id` via public API.
4. Review `type` omits `gitlab-ci` / `jenkins` (policy resource types include them).
5. No dedicated dashboard aggregate endpoints — derive from bounded list calls.
6. Artifact list has no type/date/creator query filters — filter client-side within page or omit.
7. Sort query helpers exist in schemas but are unused by routes.

## Providers

`gemini` | `llama` | `mistral`

## SSE events

`conversation` → `token`* → `completed` | `error`; ignore `heartbeat`.
