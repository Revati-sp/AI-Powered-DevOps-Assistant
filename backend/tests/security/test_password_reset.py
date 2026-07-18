from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import extract_token_from_email


async def _register_user(
    client: AsyncClient,
    *,
    username: str,
    email: str,
    password: str = "DevOpsPass123!",
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert response.status_code == 200, response.text


async def _login(
    client: AsyncClient,
    *,
    username: str,
    password: str = "DevOpsPass123!",
) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_forgot_password_no_enumeration(
    client: AsyncClient,
    email_outbox: list,
) -> None:
    await _register_user(client, username="resetuser", email="reset@example.com")

    known = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset@example.com"},
    )
    unknown = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "missing@example.com"},
    )

    assert known.status_code == 200
    assert unknown.status_code == 200
    assert known.json()["message"] == unknown.json()["message"]
    assert len(email_outbox) == 1
    assert email_outbox[0].to == "reset@example.com"


@pytest.mark.asyncio
async def test_reset_password_success_and_reuse_rejected(
    client: AsyncClient,
    email_outbox: list,
) -> None:
    await _register_user(client, username="resetok", email="resetok@example.com")
    await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "resetok@example.com"},
    )
    token = extract_token_from_email(email_outbox[-1].body_text)

    reset = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "NewSecurePass1!"},
    )
    assert reset.status_code == 200, reset.text

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "resetok", "password": "NewSecurePass1!"},
    )
    assert login.status_code == 200

    reuse = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "AnotherSecure1!"},
    )
    assert reuse.status_code == 401


@pytest.mark.asyncio
async def test_refresh_revoked_after_password_reset(
    client: AsyncClient,
    email_outbox: list,
) -> None:
    await _register_user(client, username="revokeuser", email="revoke@example.com")
    tokens = await _login(client, username="revokeuser")
    refresh_token = tokens["refresh_token"]

    await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "revoke@example.com"},
    )
    token = extract_token_from_email(email_outbox[-1].body_text)
    reset = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "ResetSecurePass1!"},
    )
    assert reset.status_code == 200

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh.status_code == 401


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient) -> None:
    await _register_user(client, username="changepw", email="changepw@example.com")
    tokens = await _login(client, username="changepw")

    change = await client.post(
        "/api/v1/auth/change-password",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
            "X-Refresh-Token": tokens["refresh_token"],
        },
        json={
            "current_password": "DevOpsPass123!",
            "new_password": "ChangedSecure1!",
        },
    )
    assert change.status_code == 200, change.text

    old_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "changepw", "password": "DevOpsPass123!"},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "changepw", "password": "ChangedSecure1!"},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_verify_email(client: AsyncClient, email_outbox: list) -> None:
    await _register_user(client, username="verifyme", email="verify@example.com")
    tokens = await _login(client, username="verifyme")

    send = await client.post(
        "/api/v1/auth/send-verification",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert send.status_code == 200, send.text
    token = extract_token_from_email(email_outbox[-1].body_text)

    verify = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["data"]["email_verified_at"] is not None

    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["data"]["email_verified_at"] is not None
