from __future__ import annotations

import pytest
from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token, hash_refresh_token
from httpx import AsyncClient
from jose import jwt


async def _register_and_login(
    client: AsyncClient,
    *,
    username: str = "hardened",
    email: str = "hardened@example.com",
    password: str = "DevOpsPass123!",
) -> dict[str, str]:
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert register.status_code == 200, register.text

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()


@pytest.mark.asyncio
async def test_login_returns_token_pair(client: AsyncClient) -> None:
    tokens = await _register_and_login(
        client, username="pairuser", email="pair@example.com"
    )
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == get_settings().access_token_expire_minutes * 60


@pytest.mark.asyncio
async def test_access_token_claims(client: AsyncClient) -> None:
    tokens = await _register_and_login(
        client, username="claimsuser", email="claims@example.com"
    )
    settings = get_settings()
    payload = decode_token(tokens["access_token"], expected_type="access")

    assert payload["iss"] == settings.jwt_issuer
    assert payload["aud"] == settings.jwt_audience
    assert payload["token_type"] == "access"
    assert payload["jti"]
    assert payload["sub"]
    assert payload["iat"]
    assert payload["nbf"]
    assert payload["exp"]


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient) -> None:
    tokens = await _register_and_login(
        client, username="rotateuser", email="rotate@example.com"
    )
    old_refresh = tokens["refresh_token"]

    refreshed = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refreshed.status_code == 200, refreshed.text
    body = refreshed.json()
    assert body["access_token"] != tokens["access_token"]
    assert body["refresh_token"] != old_refresh

    reuse = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert reuse.status_code == 401
    assert reuse.json()["error"]["message"] == "Invalid authentication credentials."


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    tokens = await _register_and_login(
        client, username="logoutuser", email="logout@example.com"
    )
    refresh_token = tokens["refresh_token"]

    logout = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout.status_code == 200, logout.text

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh.status_code == 401


@pytest.mark.asyncio
async def test_logout_all_revokes_sessions(client: AsyncClient) -> None:
    tokens = await _register_and_login(
        client, username="alloutuser", email="allout@example.com"
    )
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    logout_all = await client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_all.status_code == 200, logout_all.text

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh.status_code == 401


@pytest.mark.asyncio
async def test_register_rejects_weak_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "password123456",
        },
    )
    assert response.status_code == 422
    assert "Password does not meet security requirements" in response.text


@pytest.mark.asyncio
async def test_register_rejects_short_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "short@example.com",
            "username": "shortuser",
            "password": "short1",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_failure_uses_generic_error(client: AsyncClient) -> None:
    await _register_and_login(
        client, username="genericuser", email="generic@example.com"
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "genericuser", "password": "WrongPass123!"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid authentication credentials."


@pytest.mark.asyncio
async def test_bearer_access_token_still_works(client: AsyncClient) -> None:
    tokens = await _register_and_login(
        client, username="beareruser", email="bearer@example.com"
    )
    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["data"]["username"] == "beareruser"


@pytest.mark.asyncio
async def test_refresh_token_hash_uses_pepper() -> None:
    raw = "sample-refresh-token"
    digest = hash_refresh_token(raw)
    assert len(digest) == 64
    assert digest != raw


@pytest.mark.asyncio
async def test_wrong_token_type_rejected(client: AsyncClient) -> None:
    tokens = await _register_and_login(
        client, username="typeuser", email="type@example.com"
    )
    with pytest.raises(UnauthorizedError):
        decode_token(tokens["refresh_token"], expected_type="access")

    settings = get_settings()
    wrong_type = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "jti": "test-jti",
            "token_type": "access",
            "iat": 1,
            "nbf": 1,
            "exp": 9999999999,
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": wrong_type},
    )
    assert refresh.status_code == 401


@pytest.mark.asyncio
async def test_legacy_style_access_token_without_claims_rejected(
    client: AsyncClient,
) -> None:
    await _register_and_login(client, username="legacyuser", email="legacy@example.com")
    settings = get_settings()
    legacy_only = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "exp": 9999999999,
            "iat": 1,
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {legacy_only}"},
    )
    assert me.status_code == 401
