# Authentication

The API uses JWT access tokens for request authorization and opaque refresh tokens for session renewal. Refresh state is stored server-side.

## Endpoints

| Method | Path | Auth required | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | No | Create account |
| POST | `/api/v1/auth/login` | No | OAuth2 password flow; returns token pair |
| POST | `/api/v1/auth/refresh` | No | Rotate refresh token; returns new pair |
| POST | `/api/v1/auth/logout` | No | Revoke single refresh token |
| POST | `/api/v1/auth/logout-all` | Yes (access token) | Revoke all refresh tokens for user |

Login and refresh return a top-level `TokenPairResponse` (OAuth2-compatible):

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Protected routes expect `Authorization: Bearer <access_token>`.

## Access tokens

- Short-lived JWT (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 60).
- Claims include `sub` (user ID), `role`, `username`, `iss`, `aud`, `exp`, and `type=access`.
- Validated on every protected request via `CurrentUser` dependency.

## Refresh tokens

- Long-lived JWT-shaped token (`REFRESH_TOKEN_EXPIRE_DAYS`, default 14) with `type=refresh`, `jti`, and `family_id`.
- Only an HMAC hash (`REFRESH_TOKEN_PEPPER`) is stored in `refresh_tokens`.
- Each login creates a new token family (`family_id`).

## Rotation

On `POST /api/v1/auth/refresh`:

1. Decode and validate the refresh JWT.
2. Load the token row by `jti` (row-level lock).
3. Verify hash, expiry, and user still active.
4. Mark the old row `used_at`.
5. Issue a new refresh token in the **same family**.
6. Return a new access + refresh pair.

## Reuse detection

If a refresh token is presented after it was already used or revoked, the entire **family** is revoked (`revoke_family`, reason `reuse_detected`). An audit event `user.token.reuse_detected` is recorded. The client receives a generic `401` with `INVALID_CREDENTIALS`.

This mitigates refresh token theft: a stolen old token triggers family revocation when the legitimate client rotates.

## Logout

**Single session** — `POST /api/v1/auth/logout` with `{ "refresh_token": "..." }`:

- Invalid or unknown tokens are ignored (idempotent).
- Valid token is revoked with reason `logout`.
- Audit event `user.logout` is recorded.

**All sessions** — `POST /api/v1/auth/logout-all` with a valid access token:

- Revokes every active refresh token for the user (`logout_all`).
- Audit event `user.logout_all` includes `revoked_count`.

## Configuration

See grouped variables in `backend/.env.example`:

- `SECRET_KEY`, `JWT_*`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`, `REFRESH_TOKEN_PEPPER`
- `PASSWORD_*` settings

Production requires strong non-default secrets (see [Security](security.md)).
