from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _register_and_login(
    client: AsyncClient,
    *,
    username: str,
    email: str,
    password: str = "DevOpsPass123!",
) -> dict:
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
async def test_sessions_list_and_mark_current(client: AsyncClient) -> None:
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "sess@example.com",
            "username": "sessuser",
            "password": "DevOpsPass123!",
        },
    )
    assert register.status_code == 200, register.text

    first_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "sessuser", "password": "DevOpsPass123!"},
    )
    assert first_login.status_code == 200, first_login.text
    first = first_login.json()

    second_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "sessuser", "password": "DevOpsPass123!"},
    )
    assert second_login.status_code == 200, second_login.text
    second = second_login.json()

    sessions = await client.get(
        "/api/v1/auth/sessions",
        headers={
            "Authorization": f"Bearer {second['access_token']}",
            "X-Refresh-Token": second["refresh_token"],
        },
    )
    assert sessions.status_code == 200, sessions.text
    body = sessions.json()["data"]
    assert len(body) >= 2
    current = [item for item in body if item["is_current"]]
    assert len(current) == 1
    assert current[0]["revoked"] is False
    assert first["refresh_token"] != second["refresh_token"]


@pytest.mark.asyncio
async def test_revoke_session(client: AsyncClient) -> None:
    tokens = await _register_and_login(
        client, username="revokesess", email="revokesess@example.com"
    )

    sessions = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    session_id = sessions.json()["data"][0]["id"]

    revoke = await client.delete(
        f"/api/v1/auth/sessions/{session_id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert revoke.status_code == 200, revoke.text

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh.status_code == 401

    listed = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    revoked_items = [item for item in listed.json()["data"] if item["id"] == session_id]
    assert revoked_items[0]["revoked"] is True


@pytest.mark.asyncio
async def test_cannot_revoke_other_users_session(client: AsyncClient) -> None:
    user_a = await _register_and_login(
        client, username="sessiona", email="sessiona@example.com"
    )
    user_b = await _register_and_login(
        client, username="sessionb", email="sessionb@example.com"
    )

    sessions_a = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {user_a['access_token']}"},
    )
    session_id = sessions_a.json()["data"][0]["id"]

    revoke = await client.delete(
        f"/api/v1/auth/sessions/{session_id}",
        headers={"Authorization": f"Bearer {user_b['access_token']}"},
    )
    assert revoke.status_code == 404
