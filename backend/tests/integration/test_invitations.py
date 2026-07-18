from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import extract_token_from_email


async def _register_and_login(
    client: AsyncClient,
    *,
    username: str,
    email: str,
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
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_org(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    name: str = "Invite Team",
    slug: str | None = None,
) -> dict:
    payload: dict[str, str] = {"name": name}
    if slug is not None:
        payload["slug"] = slug
    response = await client.post("/api/v1/organizations", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["data"]


@pytest.mark.asyncio
async def test_invite_create_accept_decline_revoke(
    client: AsyncClient,
    email_outbox: list,
) -> None:
    owner_headers = await _register_and_login(
        client, username="invowner", email="invowner@example.com"
    )
    invitee_headers = await _register_and_login(
        client, username="invitee", email="invitee@example.com"
    )
    org = await _create_org(client, owner_headers, slug="invite-team")

    create = await client.post(
        f"/api/v1/organizations/{org['id']}/invitations",
        json={"email": "invitee@example.com", "role": "member"},
        headers=owner_headers,
    )
    assert create.status_code == 200, create.text
    invitation_id = create.json()["data"]["id"]
    assert len(email_outbox) == 1

    listed = await client.get(
        f"/api/v1/organizations/{org['id']}/invitations",
        headers=owner_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    token = extract_token_from_email(email_outbox[-1].body_text)
    accept = await client.post(
        "/api/v1/invitations/accept",
        json={"token": token},
        headers=invitee_headers,
    )
    assert accept.status_code == 200, accept.text
    assert accept.json()["data"]["organization_id"] == org["id"]

    members = await client.get(
        f"/api/v1/organizations/{org['id']}/members",
        headers=owner_headers,
    )
    assert members.json()["data"]["total"] == 2

    owner_headers_b = await _register_and_login(
        client, username="declowner", email="declowner@example.com"
    )
    await _register_and_login(client, username="declinee", email="declinee@example.com")
    org_b = await _create_org(client, owner_headers_b, slug="decline-team")
    await client.post(
        f"/api/v1/organizations/{org_b['id']}/invitations",
        json={"email": "declinee@example.com", "role": "viewer"},
        headers=owner_headers_b,
    )
    decline_token = extract_token_from_email(email_outbox[-1].body_text)
    decline = await client.post(
        "/api/v1/invitations/decline",
        json={"token": decline_token},
    )
    assert decline.status_code == 200

    owner_headers_c = await _register_and_login(
        client, username="revowner", email="revowner@example.com"
    )
    org_c = await _create_org(client, owner_headers_c, slug="revoke-team")
    pending = await client.post(
        f"/api/v1/organizations/{org_c['id']}/invitations",
        json={"email": "pending@example.com", "role": "member"},
        headers=owner_headers_c,
    )
    pending_id = pending.json()["data"]["id"]
    revoke = await client.delete(
        f"/api/v1/organizations/{org_c['id']}/invitations/{pending_id}",
        headers=owner_headers_c,
    )
    assert revoke.status_code == 200

    resend = await client.post(
        f"/api/v1/organizations/{org['id']}/invitations/{invitation_id}/resend",
        headers=owner_headers,
    )
    assert resend.status_code == 409


@pytest.mark.asyncio
async def test_invitation_idor(client: AsyncClient, email_outbox: list) -> None:
    owner_a = await _register_and_login(
        client, username="orga", email="orga@example.com"
    )
    owner_b = await _register_and_login(
        client, username="orgb", email="orgb@example.com"
    )
    org_a = await _create_org(client, owner_a, slug="org-a")
    org_b = await _create_org(client, owner_b, slug="org-b")

    created = await client.post(
        f"/api/v1/organizations/{org_a['id']}/invitations",
        json={"email": "guest@example.com", "role": "member"},
        headers=owner_a,
    )
    invitation_id = created.json()["data"]["id"]

    list_b = await client.get(
        f"/api/v1/organizations/{org_a['id']}/invitations",
        headers=owner_b,
    )
    assert list_b.status_code == 404

    revoke_b = await client.delete(
        f"/api/v1/organizations/{org_a['id']}/invitations/{invitation_id}",
        headers=owner_b,
    )
    assert revoke_b.status_code == 404

    resend_b = await client.post(
        f"/api/v1/organizations/{org_a['id']}/invitations/{invitation_id}/resend",
        headers=owner_b,
    )
    assert resend_b.status_code == 404

    create_b = await client.post(
        f"/api/v1/organizations/{org_b['id']}/invitations",
        json={"email": "guest@example.com", "role": "member"},
        headers=owner_b,
    )
    assert create_b.status_code == 200

    wrong_org_revoke = await client.delete(
        f"/api/v1/organizations/{org_b['id']}/invitations/{invitation_id}",
        headers=owner_b,
    )
    assert wrong_org_revoke.status_code == 404

    token = extract_token_from_email(email_outbox[0].body_text)
    guest_headers = await _register_and_login(
        client, username="guest", email="guest@example.com"
    )
    accept_wrong = await client.post(
        "/api/v1/invitations/accept",
        json={"token": token},
        headers=guest_headers,
    )
    assert accept_wrong.status_code == 200

    fake = await client.delete(
        f"/api/v1/organizations/{org_a['id']}/invitations/{uuid.uuid4()}",
        headers=owner_a,
    )
    assert fake.status_code == 404
