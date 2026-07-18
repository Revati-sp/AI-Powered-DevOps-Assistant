# Security

Security controls in the MVP backend span transport headers, authentication, authorization, input validation, and safe defaults for external calls.

## Response headers

When `SECURITY_HEADERS_ENABLED=true`, every response includes:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: interest-cohort=()`
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Resource-Policy: same-origin`
- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'`

HSTS is added in production when `HSTS_ENABLED=true`.

## Authentication hardening

- Passwords validated for length (min 12), common-password rejection, and username/email dissimilarity.
- Bcrypt hashing with configurable rounds; automatic rehash on login when parameters change.
- JWT access tokens signed with HS256; issuer, audience, and clock skew enforced on decode.
- Refresh tokens stored as HMAC-SHA256 hashes with a server pepper; raw tokens never persisted.
- Refresh rotation with family tracking and reuse detection (see [Authentication](authentication.md)).

## Authorization

Organization-scoped actions require membership and a role permission check via `OrganizationAuthService`. Cross-org probes return `404` rather than `403` to avoid leaking organization existence.

## Rate limiting

Redis-backed sliding-window limits by route category (auth, API, LLM, stream, upload). Health, readiness, and metrics endpoints are exempt. See `backend/README.md` for defaults.

## Upload and payload limits

- JSON body size capped by `MAX_JSON_BODY_SIZE_BYTES`.
- Log uploads validated for extension, size (`MAX_UPLOAD_SIZE_MB`), line count, and filename length.
- Artifact content size capped by `MAX_ARTIFACT_CONTENT_SIZE_BYTES`.

## LLM provider safety

- Provider base URLs must use HTTPS unless `ALLOW_INSECURE_LLM_HTTP=true` (development only).
- Private/reserved network targets blocked unless explicitly allowed.
- Optional host allowlist via `ALLOWED_LLM_HOSTS`.
- URLs with embedded credentials are rejected.

## Audit and redaction

Security-sensitive actions emit audit events. Metadata is recursively redacted before persistence (`audit_redaction` utilities).

## Production secret validation

On startup in `APP_ENV=production`, weak or default `SECRET_KEY` and `REFRESH_TOKEN_PEPPER` values are rejected.

## Dependency notes

`pip-audit` may report `ecdsa` (transitive via `python-jose`) under `PYSEC-2026-1325`. This backend signs JWTs with **HS256 only** (`JWT_ALGORITHM` allowlist); ECDSA algorithms are not used. Revisit when `python-jose` ships a fix or when migrating to an alternative JOSE library.

## MVP limitations

- Generated commands and manifests are never executed by the API.
- AI output must be treated as untrusted.
- File type validation is basic; do not expose upload endpoints to untrusted networks without additional controls.
- This project is not claimed to be fully secure, compliant, or production-certified.
