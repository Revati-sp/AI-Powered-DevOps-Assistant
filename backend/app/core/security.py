from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any, Literal
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import SAFE_JWT_ALGORITHMS, get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import UnauthorizedError, ValidationAppError

TokenType = Literal["access", "refresh"]

COMMON_PASSWORDS = frozenset(
    {
        "password",
        "password123",
        "password1234",
        "password12345",
        "password123456",
        "123456789012",
        "qwertyuiopas",
        "adminadmin12",
        "letmeinletmein",
        "welcome12345",
        "changeme1234",
        "securepass1234",
    }
)


@lru_cache
def _pwd_context() -> CryptContext:
    settings = get_settings()
    return CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=settings.password_bcrypt_rounds,
    )


def hash_password(password: str) -> str:
    return _pwd_context().hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context().verify(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    return _pwd_context().needs_update(hashed_password)


def validate_password(
    password: str,
    *,
    username: str = "",
    email: str = "",
) -> None:
    settings = get_settings()
    errors: list[str] = []

    if len(password) < settings.password_min_length:
        errors.append(
            f"Password must be at least {settings.password_min_length} characters."
        )
    if len(password) > settings.password_max_length:
        errors.append(
            f"Password must be at most {settings.password_max_length} characters."
        )

    lowered = password.lower()
    if username and lowered == username.lower():
        errors.append("Password must not match the username.")
    if email and lowered == email.lower():
        errors.append("Password must not match the email address.")

    if settings.password_reject_common and lowered in COMMON_PASSWORDS:
        errors.append("Password is too common.")

    if len(password) >= 2 and len(set(password)) == 1:
        errors.append("Password must not consist of a single repeated character.")

    if errors:
        raise ValidationAppError(
            "Password does not meet security requirements.",
            details={"password": errors},
        )


def _now() -> datetime:
    return datetime.now(UTC)


def _build_token_payload(
    subject: str | UUID,
    *,
    token_type: TokenType,
    expires_delta: timedelta,
    jti: str | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    now = _now()
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": jti or str(uuid4()),
        "token_type": token_type,
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return payload


def create_access_token(
    subject: str | UUID,
    *,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
    jti: str | None = None,
) -> str:
    settings = get_settings()
    payload = _build_token_payload(
        subject,
        token_type="access",
        expires_delta=expires_delta
        or timedelta(minutes=settings.access_token_expire_minutes),
        jti=jti,
        extra_claims=extra_claims,
    )
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return str(token)


def create_refresh_token(
    subject: str | UUID,
    *,
    jti: str | None = None,
    family_id: UUID | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    extra_claims: dict[str, Any] = {}
    if family_id is not None:
        extra_claims["family_id"] = str(family_id)
    payload = _build_token_payload(
        subject,
        token_type="refresh",
        expires_delta=expires_delta
        or timedelta(days=settings.refresh_token_expire_days),
        jti=jti,
        extra_claims=extra_claims or None,
    )
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return str(token)


def hash_refresh_token(raw_token: str) -> str:
    settings = get_settings()
    return hmac.new(
        settings.refresh_token_pepper.encode("utf-8"),
        raw_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    settings = get_settings()
    if settings.jwt_algorithm not in SAFE_JWT_ALGORITHMS:
        raise UnauthorizedError(
            "Invalid authentication credentials.",
            code=ErrorCode.UNAUTHORIZED,
        )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={
                "verify_aud": True,
                "verify_iss": True,
                "require_exp": True,
                "require_iat": True,
                "require_nbf": True,
                "require_sub": True,
                "leeway": settings.jwt_clock_skew_seconds,
            },
        )
    except JWTError as exc:
        raise UnauthorizedError(
            "Invalid authentication credentials.",
            code=ErrorCode.UNAUTHORIZED,
        ) from exc

    if not isinstance(payload, dict):
        raise UnauthorizedError(
            "Invalid authentication credentials.",
            code=ErrorCode.UNAUTHORIZED,
        )

    token_type = payload.get("token_type")
    if token_type != expected_type:
        raise UnauthorizedError(
            "Invalid authentication credentials.",
            code=ErrorCode.UNAUTHORIZED,
        )

    if not payload.get("jti"):
        raise UnauthorizedError(
            "Invalid authentication credentials.",
            code=ErrorCode.UNAUTHORIZED,
        )

    return dict(payload)


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type="access")
