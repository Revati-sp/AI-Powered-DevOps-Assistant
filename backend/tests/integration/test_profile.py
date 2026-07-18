import pytest
from app.models.audit import AuditEvent
from httpx import AsyncClient
from sqlalchemy import select


async def _register_and_login(
    client: AsyncClient, *, email: str, username: str
) -> tuple[dict[str, str], str]:
    password = "DevOpsPass123!"
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert login.status_code == 200, login.text
    body = login.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["refresh_token"]


@pytest.mark.asyncio
async def test_update_profile_and_get_me(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    update = await client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={
            "display_name": "  DevOps   Engineer  ",
            "timezone": "America/Los_Angeles",
            "job_title": "Platform Engineer",
            "avatar_url": "https://example.com/avatar.png",
        },
    )
    assert update.status_code == 200, update.text
    data = update.json()["data"]
    assert data["display_name"] == "DevOps Engineer"
    assert data["timezone"] == "America/Los_Angeles"
    assert data["job_title"] == "Platform Engineer"
    assert data["avatar_url"] == "https://example.com/avatar.png"

    me = await client.get("/api/v1/users/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["data"]["display_name"] == "DevOps Engineer"


@pytest.mark.asyncio
async def test_profile_rejects_unauthorized_fields(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"role": "admin", "email": "attacker@example.com"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_profile_rejects_taken_and_reserved_username(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _register_and_login(client, email="other@example.com", username="other-user")

    taken = await client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"username": "other-user"},
    )
    assert taken.status_code == 409

    reserved = await client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"username": "administrator"},
    )
    assert reserved.status_code == 422


@pytest.mark.asyncio
async def test_profile_update_records_audit_event(
    client: AsyncClient, auth_headers: dict[str, str], db_session
) -> None:
    response = await client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"job_title": "SRE"},
    )
    assert response.status_code == 200, response.text

    result = await db_session.execute(
        select(AuditEvent).where(AuditEvent.action == "user.profile.updated")
    )
    event = result.scalar_one()
    assert event.metadata_json == {"changed_fields": ["job_title"]}


@pytest.mark.asyncio
async def test_email_change_request_and_confirm_revokes_sessions(
    client: AsyncClient, email_outbox
) -> None:
    headers, refresh_token = await _register_and_login(
        client, email="old@example.com", username="old-user"
    )
    requested = await client.post(
        "/api/v1/users/me/email-change/request",
        headers=headers,
        json={"new_email": "new@example.com", "password": "DevOpsPass123!"},
    )
    assert requested.status_code == 200, requested.text
    assert requested.json()["data"]["message"] == (
        "If the request is valid, a confirmation email has been sent."
    )
    assert email_outbox[-1].to == "new@example.com"

    from tests.conftest import extract_token_from_email

    token = extract_token_from_email(email_outbox[-1].body_text)
    confirmed = await client.post(
        "/api/v1/users/me/email-change/confirm",
        json={"token": token},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["data"]["email"] == "new@example.com"
    assert confirmed.json()["data"]["email_verified_at"] is not None

    refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh.status_code == 401


@pytest.mark.asyncio
async def test_email_change_rejects_wrong_password(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/users/me/email-change/request",
        headers=auth_headers,
        json={"new_email": "new@example.com", "password": "incorrect-password"},
    )
    assert response.status_code == 401
