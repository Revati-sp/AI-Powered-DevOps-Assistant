# Email

## Provider

**Postmark** (SMTP) is the production email provider.

| Setting | Staging / production |
| --- | --- |
| `EMAIL_PROVIDER` | `smtp` |
| `SMTP_HOST` | `smtp.postmarkapp.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USE_TLS` | `true` |
| `SMTP_USERNAME` | Postmark Server API Token |
| `SMTP_PASSWORD` | Postmark Server API Token (same value) |
| `EMAIL_FROM_NAME` | Display name |
| `EMAIL_FROM_ADDRESS` / `SMTP_FROM_EMAIL` | Verified sender address |

Alternative SMTP-compatible providers (SendGrid, Mailgun, SES SMTP) can use the same variables with a different `SMTP_HOST`. Do not put credentials in `NEXT_PUBLIC_*`.

## Supported messages

| Flow | Method |
| --- | --- |
| Email verification | `send_email_verification` |
| Password reset | `send_password_reset` |
| Organization invitation | `send_organization_invitation` |
| Email-change confirmation | `send_email_change_confirmation` |

Links are built from `APP_PUBLIC_URL` (preferred) or `FRONTEND_BASE_URL`.

## Configuration knobs

```text
EMAIL_ENABLED
EMAIL_PROVIDER                 # smtp | console
EMAIL_FROM_NAME
EMAIL_FROM_ADDRESS
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_FROM_EMAIL
SMTP_USE_TLS
EMAIL_REQUEST_TIMEOUT_SECONDS
EMAIL_MAX_RETRIES
EMAIL_LOG_BODIES               # must stay false in staging/production
APP_PUBLIC_URL
FRONTEND_BASE_URL
```

## Local development

Use **Mailpit** (or similar) as a local SMTP capture:

```text
EMAIL_ENABLED=true
EMAIL_PROVIDER=smtp
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false
EMAIL_FROM_ADDRESS=dev@localhost
EMAIL_FROM_NAME=DevOps Assistant Local
EMAIL_LOG_BODIES=false
```

Console delivery (`EMAIL_PROVIDER=console` or SMTP unset) omits bodies unless `EMAIL_LOG_BODIES=true` **and** the environment is not staging/production.

## Safety rules

- Credentials stay server-side only.
- Staging/production reject `EMAIL_PROVIDER=console` when email is enabled.
- Do not log tokens, full bodies with one-time links, or provider response bodies.
- SMTP failures retry with short backoff (`EMAIL_MAX_RETRIES`) then raise; callers should fail safely without leaking tokens to clients.
- Disable console-style logging in production (`EMAIL_LOG_BODIES=false`).
