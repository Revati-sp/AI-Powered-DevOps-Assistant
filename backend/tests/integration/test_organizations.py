from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


async def _register_and_login(
    client: AsyncClient, *, username: str, email: str, password: str = "DevOpsPass123!"
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
    name: str = "Platform Team",
    slug: str | None = None,
) -> dict:
    payload: dict[str, str] = {"name": name}
    if slug is not None:
        payload["slug"] = slug
    response = await client.post("/api/v1/organizations", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_organization_creator_becomes_owner(client: AsyncClient) -> None:
    headers = await _register_and_login(
        client, username="owner1", email="owner1@example.com"
    )
    org = await _create_org(client, headers, name="DevOps Guild", slug="devops-guild")

    assert org["name"] == "DevOps Guild"
    assert org["slug"] == "devops-guild"

    members = await client.get(
        f"/api/v1/organizations/{org['id']}/members",
        headers=headers,
    )
    assert members.status_code == 200
    body = members.json()["data"]
    assert body["total"] == 1
    assert body["items"][0]["role"] == "owner"
    assert body["items"][0]["username"] == "owner1"


@pytest.mark.asyncio
async def test_slug_normalization(client: AsyncClient) -> None:
    headers = await _register_and_login(
        client, username="sluguser", email="slug@example.com"
    )
    org = await _create_org(client, headers, name="My Cool Team", slug="My Cool Team!!")
    assert org["slug"] == "my-cool-team"


@pytest.mark.asyncio
async def test_unique_slug_rejected(client: AsyncClient) -> None:
    headers_a = await _register_and_login(
        client, username="alice", email="alice@example.com"
    )
    headers_b = await _register_and_login(
        client, username="bob", email="bob@example.com"
    )

    await _create_org(client, headers_a, slug="shared-slug")

    duplicate = await client.post(
        "/api/v1/organizations",
        json={"name": "Other Team", "slug": "shared-slug"},
        headers=headers_b,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_list_organizations_pagination(client: AsyncClient) -> None:
    headers = await _register_and_login(
        client, username="lister", email="lister@example.com"
    )
    await _create_org(client, headers, name="Team Alpha", slug="team-alpha")
    await _create_org(client, headers, name="Team Beta", slug="team-beta")

    response = await client.get(
        "/api/v1/organizations?limit=1&offset=0",
        headers=headers,
    )
    assert response.status_code == 200
    page = response.json()["data"]
    assert page["total"] == 2
    assert len(page["items"]) == 1
    assert page["limit"] == 1
    assert page["offset"] == 0


@pytest.mark.asyncio
async def test_owner_and_admin_can_update_name(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="orgowner", email="orgowner@example.com"
    )
    admin_headers = await _register_and_login(
        client, username="orgadmin", email="orgadmin@example.com"
    )
    org = await _create_org(client, owner_headers, slug="update-team")

    add_admin = await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "orgadmin@example.com", "role": "admin"},
        headers=owner_headers,
    )
    assert add_admin.status_code == 200

    owner_update = await client.patch(
        f"/api/v1/organizations/{org['id']}",
        json={"name": "Renamed by Owner"},
        headers=owner_headers,
    )
    assert owner_update.status_code == 200
    assert owner_update.json()["data"]["name"] == "Renamed by Owner"

    admin_update = await client.patch(
        f"/api/v1/organizations/{org['id']}",
        json={"name": "Renamed by Admin"},
        headers=admin_headers,
    )
    assert admin_update.status_code == 200
    assert admin_update.json()["data"]["name"] == "Renamed by Admin"


@pytest.mark.asyncio
async def test_member_and_viewer_cannot_update(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="updowner", email="updowner@example.com"
    )
    member_headers = await _register_and_login(
        client, username="updmember", email="updmember@example.com"
    )
    viewer_headers = await _register_and_login(
        client, username="updviewer", email="updviewer@example.com"
    )
    org = await _create_org(client, owner_headers, slug="rbac-update")

    for email, role in [
        ("updmember@example.com", "member"),
        ("updviewer@example.com", "viewer"),
    ]:
        added = await client.post(
            f"/api/v1/organizations/{org['id']}/members",
            json={"email": email, "role": role},
            headers=owner_headers,
        )
        assert added.status_code == 200

    member_resp = await client.patch(
        f"/api/v1/organizations/{org['id']}",
        json={"name": "Blocked"},
        headers=member_headers,
    )
    assert member_resp.status_code == 403

    viewer_resp = await client.patch(
        f"/api/v1/organizations/{org['id']}",
        json={"name": "Blocked"},
        headers=viewer_headers,
    )
    assert viewer_resp.status_code == 403


@pytest.mark.asyncio
async def test_only_owner_can_delete(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="delowner", email="delowner@example.com"
    )
    admin_headers = await _register_and_login(
        client, username="deladmin", email="deladmin@example.com"
    )
    org = await _create_org(client, owner_headers, slug="delete-team")

    await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "deladmin@example.com", "role": "admin"},
        headers=owner_headers,
    )

    admin_delete = await client.delete(
        f"/api/v1/organizations/{org['id']}",
        headers=admin_headers,
    )
    assert admin_delete.status_code == 403

    owner_delete = await client.delete(
        f"/api/v1/organizations/{org['id']}",
        headers=owner_headers,
    )
    assert owner_delete.status_code == 200

    get_resp = await client.get(
        f"/api/v1/organizations/{org['id']}",
        headers=owner_headers,
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_add_member_and_duplicate_rejection(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="addowner", email="addowner@example.com"
    )
    await _register_and_login(
        client, username="newmember", email="newmember@example.com"
    )
    org = await _create_org(client, owner_headers, slug="member-team")

    add = await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "newmember@example.com", "role": "member"},
        headers=owner_headers,
    )
    assert add.status_code == 200
    assert add.json()["data"]["role"] == "member"

    duplicate = await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "newmember@example.com", "role": "viewer"},
        headers=owner_headers,
    )
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_final_owner_protection(client: AsyncClient) -> None:
    headers = await _register_and_login(
        client, username="soloowner", email="soloowner@example.com"
    )
    org = await _create_org(client, headers, slug="solo-owner-team")
    owner_id = (
        await client.get(
            f"/api/v1/organizations/{org['id']}/members",
            headers=headers,
        )
    ).json()["data"]["items"][0]["user_id"]

    demote = await client.patch(
        f"/api/v1/organizations/{org['id']}/members/{owner_id}",
        json={"role": "admin"},
        headers=headers,
    )
    assert demote.status_code == 403

    remove = await client.delete(
        f"/api/v1/organizations/{org['id']}/members/{owner_id}",
        headers=headers,
    )
    assert remove.status_code == 403


@pytest.mark.asyncio
async def test_admin_cannot_modify_owner(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="modowner", email="modowner@example.com"
    )
    admin_headers = await _register_and_login(
        client, username="modadmin", email="modadmin@example.com"
    )
    org = await _create_org(client, owner_headers, slug="admin-mod-team")

    await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "modadmin@example.com", "role": "admin"},
        headers=owner_headers,
    )

    owner_id = (
        await client.get(
            f"/api/v1/organizations/{org['id']}/members",
            headers=owner_headers,
        )
    ).json()["data"]["items"][0]["user_id"]

    demote = await client.patch(
        f"/api/v1/organizations/{org['id']}/members/{owner_id}",
        json={"role": "member"},
        headers=admin_headers,
    )
    assert demote.status_code == 403

    remove = await client.delete(
        f"/api/v1/organizations/{org['id']}/members/{owner_id}",
        headers=admin_headers,
    )
    assert remove.status_code == 403


@pytest.mark.asyncio
async def test_cross_org_access_denied(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="orgaowner", email="orgaowner@example.com"
    )
    outsider_headers = await _register_and_login(
        client, username="outsider", email="outsider@example.com"
    )
    org = await _create_org(client, owner_headers, slug="private-team")

    get_resp = await client.get(
        f"/api/v1/organizations/{org['id']}",
        headers=outsider_headers,
    )
    assert get_resp.status_code == 404

    guessed = await client.get(
        f"/api/v1/organizations/{uuid.uuid4()}",
        headers=outsider_headers,
    )
    assert guessed.status_code == 404


@pytest.mark.asyncio
async def test_viewer_cannot_manage_members(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="viewowner", email="viewowner@example.com"
    )
    viewer_headers = await _register_and_login(
        client, username="viewonly", email="viewonly@example.com"
    )
    await _register_and_login(client, username="target", email="target@example.com")
    org = await _create_org(client, owner_headers, slug="viewer-team")

    await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "viewonly@example.com", "role": "viewer"},
        headers=owner_headers,
    )

    add = await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "target@example.com", "role": "member"},
        headers=viewer_headers,
    )
    assert add.status_code == 403


@pytest.mark.asyncio
async def test_change_member_role_and_remove(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="roleowner", email="roleowner@example.com"
    )
    await _register_and_login(client, username="roleuser", email="roleuser@example.com")
    org = await _create_org(client, owner_headers, slug="role-team")

    added = await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "roleuser@example.com", "role": "member"},
        headers=owner_headers,
    )
    user_id = added.json()["data"]["user_id"]

    updated = await client.patch(
        f"/api/v1/organizations/{org['id']}/members/{user_id}",
        json={"role": "admin"},
        headers=owner_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["role"] == "admin"

    removed = await client.delete(
        f"/api/v1/organizations/{org['id']}/members/{user_id}",
        headers=owner_headers,
    )
    assert removed.status_code == 200

    members = await client.get(
        f"/api/v1/organizations/{org['id']}/members",
        headers=owner_headers,
    )
    assert members.json()["data"]["total"] == 1
