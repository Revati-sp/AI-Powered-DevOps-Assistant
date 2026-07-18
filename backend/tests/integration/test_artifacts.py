from __future__ import annotations

import hashlib

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_artifact_list_type_sort_and_content_omission(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    for name, artifact_type in [
        ("Zulu Manifest", "kubernetes"),
        ("Alpha Dockerfile", "dockerfile"),
    ]:
        created = await client.post(
            "/api/v1/artifacts",
            headers=auth_headers,
            json={
                "name": name,
                "artifact_type": artifact_type,
                "content": "secret-content",
            },
        )
        assert created.status_code == 200, created.text

    listed = await client.get(
        "/api/v1/artifacts",
        headers=auth_headers,
        params={"artifact_type": "dockerfile", "sort_by": "name", "sort_order": "asc"},
    )
    assert listed.status_code == 200, listed.text
    items = listed.json()["data"]["items"]
    assert [item["name"] for item in items] == ["Alpha Dockerfile"]
    assert "content" not in items[0]


@pytest.mark.asyncio
async def test_create_personal_artifact_with_version_one(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/artifacts",
        headers=auth_headers,
        json={
            "name": "Test Artifact",
            "artifact_type": "dockerfile",
            "content": "FROM alpine:3.20\nUSER app\n",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["current_version_number"] == 1
    assert data["current_version"]["version_number"] == 1
    expected_hash = hashlib.sha256(b"FROM alpine:3.20\nUSER app\n").hexdigest()
    assert data["current_version"]["content_hash"] == expected_hash


@pytest.mark.asyncio
async def test_add_version_and_skip_duplicate_content(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create = await client.post(
        "/api/v1/artifacts",
        headers=auth_headers,
        json={
            "name": "Versioned",
            "artifact_type": "kubernetes",
            "content": "v1-content",
        },
    )
    artifact_id = create.json()["data"]["id"]

    add_v2 = await client.post(
        f"/api/v1/artifacts/{artifact_id}/versions",
        headers=auth_headers,
        json={"content": "v2-content"},
    )
    assert add_v2.json()["data"]["version_number"] == 2

    duplicate = await client.post(
        f"/api/v1/artifacts/{artifact_id}/versions",
        headers=auth_headers,
        json={"content": "v2-content"},
    )
    assert duplicate.json()["data"]["version_number"] == 2


@pytest.mark.asyncio
async def test_restore_creates_new_version(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create = await client.post(
        "/api/v1/artifacts",
        headers=auth_headers,
        json={
            "name": "Restore Test",
            "artifact_type": "terraform",
            "content": "version-one",
        },
    )
    artifact_id = create.json()["data"]["id"]

    await client.post(
        f"/api/v1/artifacts/{artifact_id}/versions",
        headers=auth_headers,
        json={"content": "version-two"},
    )

    restore = await client.post(
        f"/api/v1/artifacts/{artifact_id}/versions/1/restore",
        headers=auth_headers,
    )
    body = restore.json()["data"]
    assert body["restored_from_version"] == 1
    assert body["new_version"]["version_number"] == 3
    assert body["new_version"]["content"] == "version-one"


@pytest.mark.asyncio
async def test_unified_diff(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    create = await client.post(
        "/api/v1/artifacts",
        headers=auth_headers,
        json={
            "name": "Diff Test",
            "artifact_type": "dockerfile",
            "content": "line-a\n",
        },
    )
    artifact_id = create.json()["data"]["id"]
    await client.post(
        f"/api/v1/artifacts/{artifact_id}/versions",
        headers=auth_headers,
        json={"content": "line-b\n"},
    )

    diff = await client.get(
        f"/api/v1/artifacts/{artifact_id}/diff",
        headers=auth_headers,
        params={"from_version": 1, "to_version": 2},
    )
    assert diff.status_code == 200
    assert "line-a" in diff.json()["data"]["diff"]
    assert "line-b" in diff.json()["data"]["diff"]


@pytest.mark.asyncio
async def test_personal_artifact_isolation(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create = await client.post(
        "/api/v1/artifacts",
        headers=auth_headers,
        json={
            "name": "Private",
            "artifact_type": "dockerfile",
            "content": "private",
        },
    )
    artifact_id = create.json()["data"]["id"]

    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "username": "otheruser",
            "password": "DevOpsPass123!",
        },
    )
    assert other.status_code == 200
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "otheruser", "password": "DevOpsPass123!"},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    denied = await client.get(
        f"/api/v1/artifacts/{artifact_id}",
        headers=other_headers,
    )
    assert denied.status_code == 404


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


async def _create_org(client: AsyncClient, headers: dict[str, str]) -> dict:
    response = await client.post(
        "/api/v1/organizations",
        json={
            "name": "Artifact Team",
            "slug": f"artifact-team-{username_hash(headers)}",
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def username_hash(headers: dict[str, str]) -> str:
    return str(abs(hash(headers["Authorization"])) % 10_000)


@pytest.mark.asyncio
async def test_org_scoped_artifact_lifecycle(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="artowner", email="artowner@example.com"
    )
    member_headers = await _register_and_login(
        client, username="artmember", email="artmember@example.com"
    )
    org = await _create_org(client, owner_headers)

    await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "artmember@example.com", "role": "member"},
        headers=owner_headers,
    )

    create = await client.post(
        "/api/v1/artifacts",
        headers=member_headers,
        json={
            "name": "Team Dockerfile",
            "artifact_type": "dockerfile",
            "content": "FROM alpine:3.20\nUSER app\n",
            "organization_id": org["id"],
        },
    )
    assert create.status_code == 200, create.text
    artifact_id = create.json()["data"]["id"]

    listed = await client.get(
        "/api/v1/artifacts",
        headers=member_headers,
        params={"organization_id": org["id"]},
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    add_v2 = await client.post(
        f"/api/v1/artifacts/{artifact_id}/versions",
        headers=member_headers,
        json={"content": "FROM alpine:3.21\nUSER app\n"},
    )
    assert add_v2.json()["data"]["version_number"] == 2

    versions = await client.get(
        f"/api/v1/artifacts/{artifact_id}/versions",
        headers=member_headers,
    )
    assert versions.status_code == 200
    assert versions.json()["data"]["total"] == 2

    version_one = await client.get(
        f"/api/v1/artifacts/{artifact_id}/versions/1",
        headers=member_headers,
    )
    assert version_one.status_code == 200
    assert "3.20" in version_one.json()["data"]["content"]

    updated = await client.patch(
        f"/api/v1/artifacts/{artifact_id}",
        headers=member_headers,
        json={"name": "Renamed Team Dockerfile", "description": "Shared"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Renamed Team Dockerfile"

    restore = await client.post(
        f"/api/v1/artifacts/{artifact_id}/versions/1/restore",
        headers=member_headers,
    )
    assert restore.status_code == 200
    assert restore.json()["data"]["new_version"]["version_number"] == 3

    diff = await client.get(
        f"/api/v1/artifacts/{artifact_id}/diff",
        headers=member_headers,
        params={"from_version": 1, "to_version": 2},
    )
    assert diff.status_code == 200
    assert diff.json()["data"]["diff"]

    deleted = await client.delete(
        f"/api/v1/artifacts/{artifact_id}",
        headers=owner_headers,
    )
    assert deleted.status_code == 200

    gone = await client.get(
        f"/api/v1/artifacts/{artifact_id}",
        headers=owner_headers,
    )
    assert gone.status_code == 404


@pytest.mark.asyncio
async def test_viewer_cannot_create_org_artifact(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="artviewowner", email="artviewowner@example.com"
    )
    viewer_headers = await _register_and_login(
        client, username="artviewer", email="artviewer@example.com"
    )
    org = await _create_org(client, owner_headers)

    await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "artviewer@example.com", "role": "viewer"},
        headers=owner_headers,
    )

    denied = await client.post(
        "/api/v1/artifacts",
        headers=viewer_headers,
        json={
            "name": "Blocked",
            "artifact_type": "dockerfile",
            "content": "FROM alpine\n",
            "organization_id": org["id"],
        },
    )
    assert denied.status_code == 403
