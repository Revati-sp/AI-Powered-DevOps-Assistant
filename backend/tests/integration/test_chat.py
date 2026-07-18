import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_conversation_list_filters_sort_and_pagination(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    for message in ["Alpha deployment", "Beta rollout"]:
        response = await client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={"message": message, "provider": "gemini"},
        )
        assert response.status_code == 200, response.text

    filtered = await client.get(
        "/api/v1/chat/conversations",
        headers=auth_headers,
        params={"search": "Alpha", "sort_by": "title", "sort_order": "asc"},
    )
    assert filtered.status_code == 200, filtered.text
    assert [item["title"] for item in filtered.json()["data"]["items"]] == [
        "Alpha deployment"
    ]
    assert filtered.json()["data"]["items"][0]["organization_id"] is None

    provider_filtered = await client.get(
        "/api/v1/chat/conversations",
        headers=auth_headers,
        params={"provider": "gemini", "limit": 1, "offset": 0},
    )
    assert provider_filtered.status_code == 200
    page = provider_filtered.json()["data"]
    assert page["total"] == 2
    assert page["limit"] == 1
    assert page["items"][0]["provider"] == "gemini"


@pytest.mark.asyncio
async def test_chat_and_conversation_ownership(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    chat = await client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={
            "message": "Why is my Kubernetes pod in CrashLoopBackOff?",
            "conversation_id": None,
            "provider": "gemini",
        },
    )
    assert chat.status_code == 200
    data = chat.json()["data"]
    assert data["provider"] == "gemini"
    assert data["answer"]
    conversation_id = data["conversation_id"]

    listed = await client.get("/api/v1/chat/conversations", headers=auth_headers)
    assert listed.status_code == 200
    page = listed.json()["data"]
    assert page["total"] == 1
    assert len(page["items"]) == 1
    assert page["limit"] == 20
    assert page["offset"] == 0

    detail = await client.get(
        f"/api/v1/chat/conversations/{conversation_id}",
        headers=auth_headers,
    )
    assert detail.status_code == 200
    assert len(detail.json()["data"]["messages"]) == 2

    # Second user cannot access first user's conversation.
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@example.com",
            "username": "bob",
            "password": "DevOpsPass123!",
        },
    )
    bob_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "bob", "password": "DevOpsPass123!"},
    )
    bob_headers = {"Authorization": f"Bearer {bob_login.json()['access_token']}"}
    forbidden = await client.get(
        f"/api/v1/chat/conversations/{conversation_id}",
        headers=bob_headers,
    )
    assert forbidden.status_code == 404

    deleted = await client.delete(
        f"/api/v1/chat/conversations/{conversation_id}",
        headers=auth_headers,
    )
    assert deleted.status_code == 200
