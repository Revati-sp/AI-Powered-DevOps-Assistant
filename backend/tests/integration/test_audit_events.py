from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.test_organizations import _create_org, _register_and_login


@pytest.mark.asyncio
async def test_org_owner_lists_audit_events(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="auditowner", email="auditowner@example.com"
    )
    org = await _create_org(client, owner_headers, slug="audit-team")

    pack_resp = await client.post(
        f"/api/v1/organizations/{org['id']}/policy-packs",
        headers=owner_headers,
        json={
            "name": "Audit Pack",
            "description": "For audit trail",
            "is_active": True,
        },
    )
    assert pack_resp.status_code == 200

    events = await client.get(
        f"/api/v1/organizations/{org['id']}/audit-events",
        headers=owner_headers,
    )
    assert events.status_code == 200, events.text
    body = events.json()["data"]
    assert body["total"] >= 2
    actions = {item["action"] for item in body["items"]}
    assert "organization.created" in actions
    assert "policy_pack.created" in actions

    filtered = await client.get(
        f"/api/v1/organizations/{org['id']}/audit-events",
        headers=owner_headers,
        params={"action": "organization.created"},
    )
    assert filtered.status_code == 200
    assert all(
        item["action"] == "organization.created"
        for item in filtered.json()["data"]["items"]
    )


@pytest.mark.asyncio
async def test_member_cannot_read_audit_events(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="auditmemowner", email="auditmemowner@example.com"
    )
    member_headers = await _register_and_login(
        client, username="auditmember", email="auditmember@example.com"
    )
    org = await _create_org(client, owner_headers, slug="audit-member-team")

    await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "auditmember@example.com", "role": "member"},
        headers=owner_headers,
    )

    denied = await client.get(
        f"/api/v1/organizations/{org['id']}/audit-events",
        headers=member_headers,
    )
    assert denied.status_code == 403
