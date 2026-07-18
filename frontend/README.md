# Frontend — AI-Powered DevOps Assistant

Next.js App Router UI for the DevOps Assistant API. The browser talks only to Next.js route handlers; JWT tokens stay in HTTP-only cookies and are attached server-side when proxying to FastAPI.

## Stack

| Layer     | Choice                                                  |
| --------- | ------------------------------------------------------- |
| Framework | Next.js 16 (App Router), React 19, TypeScript           |
| Styling   | Tailwind CSS 4, Radix UI, shadcn-style components       |
| Data      | TanStack Query, Zod, React Hook Form                    |
| State     | Zustand (UI + workspace org)                            |
| Auth      | BFF cookies (`ada_access` / `ada_refresh`)              |
| Tests     | Vitest + Testing Library, Playwright + axe-core         |
| Runtime   | Node 22; Docker multi-stage with `output: 'standalone'` |

## Quick start

```bash
cd frontend
cp .env.example .env.local   # optional; defaults work for local API on :8000
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The API should be reachable at `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`).

Production-like local run:

```bash
npm run build && npm run start
```

## Scripts

| Script                            | Purpose                                                                        |
| --------------------------------- | ------------------------------------------------------------------------------ |
| `npm run dev`                     | Dev server                                                                     |
| `npm run build` / `start`         | Production build & serve                                                       |
| `npm run lint`                    | ESLint                                                                         |
| `npm run format` / `format:check` | Prettier                                                                       |
| `npm run typecheck`               | `tsc --noEmit`                                                                 |
| `npm test`                        | Vitest unit/integration                                                        |
| `npm run test:e2e`                | Playwright (expects a production build; starts `npm run start` unless skipped) |
| `npm run api:generate`            | Regenerate OpenAPI types from `openapi.json`                                   |

## Project structure

```
app/
  (auth)/          Login & register
  (dashboard)/     Authenticated workspace pages
  api/auth/        Cookie session routes (login, me, logout, …)
  api/bff/         Authenticated proxy to FastAPI
components/        UI, app shell, feature screens
features/          Domain APIs, schemas, hooks
hooks/             Shared hooks (auth, streaming chat)
lib/               API client, auth cookies/session, permissions, utils
providers/         Auth, theme, query client
store/             UI + workspace Zustand stores
tests/unit|integration|e2e
middleware.ts      Route guards via session cookies
```

## Environment variables

See [`.env.example`](.env.example).

| Variable                       | Scope       | Notes                                                                                           |
| ------------------------------ | ----------- | ----------------------------------------------------------------------------------------------- |
| `NEXT_PUBLIC_APP_NAME`         | Browser     | Product title                                                                                   |
| `NEXT_PUBLIC_API_BASE_URL`     | Browser     | Public API origin (docs / fallbacks). Browser data calls use `/api/bff`, not this URL directly. |
| `NEXT_PUBLIC_DEFAULT_THEME`    | Browser     | `system` \| `light` \| `dark`                                                                   |
| `NEXT_PUBLIC_ENABLE_DARK_MODE` | Browser     | Feature flag reserved for theme UX                                                              |
| `NEXT_PUBLIC_ENABLE_STORYBOOK` | Browser     | Storybook deferred                                                                              |
| `INTERNAL_API_BASE_URL`        | Server only | FastAPI base for BFF / `getCurrentUser`. Use `http://api:8000` in Compose.                      |
| `AUTH_COOKIE_SECURE`           | Server only | `true` behind HTTPS; `false` for local HTTP                                                     |

Never commit `.env` / `.env.local`. Do not put LLM API keys in the frontend — the backend owns providers.

## BFF auth model

1. Login/register hit `/api/auth/*`, which call FastAPI and set HTTP-only cookies (`ada_access`, `ada_refresh`).
2. Middleware allows protected prefixes only when a session cookie is present; unauthenticated users redirect to `/login?returnUrl=…`.
3. Browser API traffic uses `/api/bff/...`, which forwards to `INTERNAL_API_BASE_URL` with the access token. On 401, the BFF attempts refresh using the refresh cookie.
4. `/api/auth/me` resolves the current user server-side (with refresh retry).

Tokens are never stored in `localStorage`. FastAPI does not accept cookie auth directly — only Bearer tokens from the BFF.

## SSE / streaming chat

Chat streaming uses the BFF path against `/api/v1/chat/stream`. The client parses SSE events (`conversation`, `token`, `completed`, `error`; `heartbeat` ignored). See `hooks/use-streaming-chat.ts` and `docs/BACKEND_CONTRACT.md`.

## Organization context & permissions

- Workspace org is selected in the header (`OrganizationSwitcher`) and stored in Zustand (`store/workspace-store`).
- Nav and actions use `useOrgRole()` for UX gating only.
- Backend RBAC remains authoritative. Permission keys and gaps are documented in `docs/BACKEND_CONTRACT.md` and root `docs/rbac.md`.

## Generators hub

`/generators` links to Dockerfile, Kubernetes, CI/CD pipeline, and shell command generators. Each form posts through the BFF; output is editable and can be saved as an artifact when the API allows.

## Testing

**Unit / integration (Vitest)** — MSW for auth and API envelopes; no real backend.

```bash
npm test
npm run test:coverage
```

**E2E (Playwright)** — mocked `/api/auth/*` and `/api/bff/**` via `page.route`; session cookies set with `context.addCookies`. No real LLM keys or backend required.

```bash
npm run build
npx playwright install chromium   # first time
npm run test:e2e
```

In CI, build runs before e2e; Playwright’s `webServer` runs `npm run start:standalone` (copies `public` + `.next/static` into the standalone output, then `node server.js`). Set `PLAYWRIGHT_SKIP_WEBSERVER=1` if you already serve the app. Accessibility: axe-core on the login page (`@axe-core/playwright`; color-contrast disabled until primary tokens meet AA).

## Docker

Multi-stage image (`frontend/Dockerfile`):

1. **deps** — `node:22-alpine`, `npm ci`
2. **builder** — source + `NEXT_TELEMETRY_DISABLED=1` + `npm run build`
3. **runner** — non-root `nextjs`, standalone output, `public`, `.next/static`, healthcheck on `:3000`

```bash
# From repo root (api + db + redis + worker + frontend)
docker compose up --build

# Frontend image only
docker build -t devops-frontend ./frontend
docker run --rm -p 3000:3000 \
  -e INTERNAL_API_BASE_URL=http://host.docker.internal:8000 \
  -e NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 \
  -e AUTH_COOKIE_SECURE=false \
  devops-frontend
```

`.dockerignore` excludes `node_modules`, `.next`, `.env*`, coverage, Playwright artifacts, and `.git`. Env files are never copied into the image.

## Security limitations (frontend)

- Cookies default to `Secure` in production unless `AUTH_COOKIE_SECURE` overrides — use HTTPS in prod.
- BFF trusts network reachability to `INTERNAL_API_BASE_URL`; keep that URL private in deployments.
- Client-side RBAC is cosmetic; always enforce on the API.
- Generated infra/commands are preview-only; the UI does not execute them.
- XSS: markdown is sanitized (`rehype-sanitize`); still treat model output as untrusted.
- No frontend LLM keys; do not add provider secrets to `NEXT_PUBLIC_*`.
- E2E mocks are not a security boundary — they only isolate CI from a live API.

## Related docs

- [Backend README](../backend/README.md)
- [Backend contract notes](docs/BACKEND_CONTRACT.md)
- [Root README](../README.md)
- [Architecture](../docs/architecture.md) · [Auth](../docs/authentication.md) · [RBAC](../docs/rbac.md)
