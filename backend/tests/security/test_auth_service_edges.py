from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    validate_password,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import GENERIC_AUTH_ERROR, AuthService
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_conflict_email_and_username(db_session: AsyncSession) -> None:
    svc = AuthService(db_session)
    await svc.register(
        RegisterRequest(
            email="dup@example.com",
            username="dupuser",
            password="DevOpsPass123!",
        )
    )
    with pytest.raises(ConflictError, match="Email already registered"):
        await svc.register(
            RegisterRequest(
                email="dup@example.com",
                username="otheruser",
                password="DevOpsPass123!",
            )
        )
    with pytest.raises(ConflictError, match="Username already taken"):
        await svc.register(
            RegisterRequest(
                email="other@example.com",
                username="dupuser",
                password="DevOpsPass123!",
            )
        )


@pytest.mark.asyncio
async def test_inactive_user_login_is_generic(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        email="inactive@example.com",
        username="inactiveuser",
        hashed_password=hash_password("DevOpsPass123!"),
    )
    user.is_active = False
    await db_session.flush()

    svc = AuthService(db_session)
    with pytest.raises(UnauthorizedError, match=GENERIC_AUTH_ERROR):
        await svc.login(
            LoginRequest(username="inactiveuser", password="DevOpsPass123!")
        )


@pytest.mark.asyncio
async def test_password_rehash_on_login(db_session: AsyncSession) -> None:
    weak_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)
    users = UserRepository(db_session)
    user = await users.create(
        email="rehash@example.com",
        username="rehashuser",
        hashed_password=weak_ctx.hash("DevOpsPass123!"),
    )
    old_hash = user.hashed_password

    svc = AuthService(db_session)
    tokens = await svc.login(
        LoginRequest(username="rehashuser", password="DevOpsPass123!")
    )
    assert tokens.access_token
    await db_session.refresh(user)
    assert user.hashed_password != old_hash


@pytest.mark.asyncio
async def test_refresh_expired_token_rejected(db_session: AsyncSession) -> None:
    svc = AuthService(db_session)
    user = await svc.register(
        RegisterRequest(
            email="exp@example.com",
            username="expuser",
            password="DevOpsPass123!",
        )
    )
    jti = str(uuid4())
    family_id = uuid4()
    raw = create_refresh_token(user.id, jti=jti, family_id=family_id)
    await RefreshTokenRepository(db_session).create(
        user_id=user.id,
        family_id=family_id,
        token_hash=hash_refresh_token(raw),
        jti=jti,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )

    with pytest.raises(UnauthorizedError, match=GENERIC_AUTH_ERROR):
        await svc.refresh(raw)


@pytest.mark.asyncio
async def test_refresh_hash_mismatch_rejected(db_session: AsyncSession) -> None:
    svc = AuthService(db_session)
    user = await svc.register(
        RegisterRequest(
            email="hash@example.com",
            username="hashuser",
            password="DevOpsPass123!",
        )
    )
    jti = str(uuid4())
    family_id = uuid4()
    raw = create_refresh_token(user.id, jti=jti, family_id=family_id)
    await RefreshTokenRepository(db_session).create(
        user_id=user.id,
        family_id=family_id,
        token_hash=hash_refresh_token("different-raw-token"),
        jti=jti,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    with pytest.raises(UnauthorizedError, match=GENERIC_AUTH_ERROR):
        await svc.refresh(raw)


@pytest.mark.asyncio
async def test_refresh_unknown_jti_rejected(db_session: AsyncSession) -> None:
    svc = AuthService(db_session)
    user = await svc.register(
        RegisterRequest(
            email="nojti@example.com",
            username="nojtiuser",
            password="DevOpsPass123!",
        )
    )
    raw = create_refresh_token(user.id, jti=str(uuid4()), family_id=uuid4())
    with pytest.raises(UnauthorizedError, match=GENERIC_AUTH_ERROR):
        await svc.refresh(raw)


@pytest.mark.asyncio
async def test_refresh_inactive_user_rejected(db_session: AsyncSession) -> None:
    svc = AuthService(db_session)
    await svc.register(
        RegisterRequest(
            email="refinact@example.com",
            username="refinact",
            password="DevOpsPass123!",
        )
    )
    tokens = await svc.login(
        LoginRequest(username="refinact", password="DevOpsPass123!")
    )
    users = UserRepository(db_session)
    user = await users.get_by_username("refinact")
    assert user is not None
    user.is_active = False
    await db_session.flush()

    with pytest.raises(UnauthorizedError, match=GENERIC_AUTH_ERROR):
        await svc.refresh(tokens.refresh_token)


@pytest.mark.asyncio
async def test_logout_idempotent_for_invalid_and_unknown(
    db_session: AsyncSession,
) -> None:
    svc = AuthService(db_session)
    await svc.logout("not-a-jwt")
    user = await svc.register(
        RegisterRequest(
            email="logoutid@example.com",
            username="logoutid",
            password="DevOpsPass123!",
        )
    )
    jti = str(uuid4())
    family_id = uuid4()
    raw = create_refresh_token(user.id, jti=jti, family_id=family_id)
    # Unknown jti
    await svc.logout(raw)
    # Hash mismatch
    await RefreshTokenRepository(db_session).create(
        user_id=user.id,
        family_id=family_id,
        token_hash=hash_refresh_token("other"),
        jti=jti,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    await svc.logout(raw)


@pytest.mark.asyncio
async def test_get_current_user_response(db_session: AsyncSession) -> None:
    svc = AuthService(db_session)
    user = await svc.register(
        RegisterRequest(
            email="me@example.com",
            username="meuser",
            password="DevOpsPass123!",
        )
    )
    model = await UserRepository(db_session).get_by_id(user.id)
    assert model is not None
    response = await svc.get_current_user_response(model)
    assert response.username == "meuser"


def test_password_rejects_repeated_character() -> None:
    with pytest.raises(Exception, match="security requirements"):
        validate_password("aaaaaaaaaaaa")


def test_password_accepts_long_passphrase() -> None:
    validate_password("correct horse battery staple extra words")


def test_password_rejects_username_match() -> None:
    with pytest.raises(Exception, match="security requirements"):
        validate_password("SameAsUsername", username="SameAsUsername")


def test_as_utc_naive_and_aware() -> None:
    from app.services.auth_service import _as_utc

    naive = datetime(2024, 1, 1, 12, 0, 0)
    aware = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert _as_utc(naive).tzinfo is not None
    assert _as_utc(aware).tzinfo is not None


@pytest.mark.asyncio
async def test_refresh_subject_mismatch_rejected(db_session: AsyncSession) -> None:
    svc = AuthService(db_session)
    user_a = await svc.register(
        RegisterRequest(
            email="suba@example.com",
            username="suba",
            password="DevOpsPass123!",
        )
    )
    user_b = await svc.register(
        RegisterRequest(
            email="subb@example.com",
            username="subb",
            password="DevOpsPass123!",
        )
    )
    jti = str(uuid4())
    family_id = uuid4()
    # Token claims user_b, persisted record belongs to user_a
    raw = create_refresh_token(user_b.id, jti=jti, family_id=family_id)
    await RefreshTokenRepository(db_session).create(
        user_id=user_a.id,
        family_id=family_id,
        token_hash=hash_refresh_token(raw),
        jti=jti,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    with pytest.raises(UnauthorizedError, match=GENERIC_AUTH_ERROR):
        await svc.refresh(raw)
