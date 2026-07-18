import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_login_and_me(client: AsyncClient) -> None:
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "username": "alice",
            "password": "DevOpsPass123!",
        },
    )
    assert register.status_code == 200
    body = register.json()
    assert body["success"] is True
    assert body["data"]["username"] == "alice"
    assert "hashed_password" not in body["data"]

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "alice", "password": "DevOpsPass123!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["data"]["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
