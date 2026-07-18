import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_personal_dashboard_summary_and_activity(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    chat = await client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"message": "Check deployment health", "provider": "gemini"},
    )
    assert chat.status_code == 200, chat.text
    artifact = await client.post(
        "/api/v1/artifacts",
        headers=auth_headers,
        json={
            "name": "Dashboard Dockerfile",
            "artifact_type": "dockerfile",
            "content": "FROM alpine:3.20\nUSER app\n",
        },
    )
    assert artifact.status_code == 200, artifact.text

    summary = await client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert summary.status_code == 200, summary.text
    data = summary.json()["data"]
    assert data["conversations"] == {"total": 1, "recent": 1}
    assert data["artifacts"]["total"] == 1
    assert data["organization"] is None

    activity = await client.get("/api/v1/dashboard/activity", headers=auth_headers)
    assert activity.status_code == 200, activity.text
    assert {item["type"] for item in activity.json()["data"]["items"]} >= {
        "conversation",
        "artifact",
    }


@pytest.mark.asyncio
async def test_dashboard_org_scope_requires_membership(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={"name": "Dashboard Team", "slug": "dashboard-team"},
    )
    assert created.status_code == 200, created.text
    organization_id = created.json()["data"]["id"]

    other_register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dashboard-other@example.com",
            "username": "dashboardother",
            "password": "DevOpsPass123!",
        },
    )
    assert other_register.status_code == 200
    other_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "dashboardother", "password": "DevOpsPass123!"},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    denied = await client.get(
        "/api/v1/dashboard/summary",
        headers=other_headers,
        params={"organization_id": organization_id},
    )
    assert denied.status_code == 404
