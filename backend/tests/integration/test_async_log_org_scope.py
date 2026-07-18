from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from app.models.analysis import Analysis
from app.models.audit import AuditEvent
from app.models.background_task import BackgroundTask
from app.workers.celery_app import celery_app
from httpx import AsyncClient
from sqlalchemy import select


@pytest.fixture(autouse=True)
def mock_celery_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    celery_app.conf.task_always_eager = False

    def _delay(*args: Any, **kwargs: Any) -> Any:
        class AsyncResult:
            id = f"celery-{uuid4().hex[:12]}"

        return AsyncResult()

    from app.workers import tasks as worker_tasks

    monkeypatch.setattr(worker_tasks.analyze_logs_task, "delay", _delay)


async def _register_login(
    client: AsyncClient, *, email: str, username: str
) -> dict[str, str]:
    password = "DevOpsPass123!"
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
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _create_org(client: AsyncClient, headers: dict[str, str]) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": "Log Org", "slug": f"log-org-{uuid4().hex[:8]}"},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


@pytest.mark.asyncio
async def test_personal_async_log_analysis_without_organization(
    client: AsyncClient, auth_headers: dict[str, str], db_session
) -> None:
    response = await client.post(
        "/api/v1/logs/analyze/async",
        headers=auth_headers,
        json={"content": "CrashLoopBackOff\nERROR: Job failed\n", "provider": "gemini"},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["organization_id"] is None
    assert data["task_id"]
    assert data["analysis_id"] is not None

    task = await db_session.get(BackgroundTask, UUID(data["task_id"]))
    assert task is not None
    assert task.organization_id is None

    analysis = await db_session.get(Analysis, UUID(data["analysis_id"]))
    assert analysis is not None
    assert analysis.organization_id is None


@pytest.mark.asyncio
async def test_organization_async_log_analysis_as_owner(
    client: AsyncClient, auth_headers: dict[str, str], db_session
) -> None:
    org = await _create_org(client, auth_headers)
    response = await client.post(
        "/api/v1/logs/analyze/async",
        headers=auth_headers,
        json={
            "content": "OOMKilled\nCrashLoopBackOff\n",
            "provider": "gemini",
            "organization_id": org["id"],
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["organization_id"] == org["id"]

    task = await db_session.get(BackgroundTask, UUID(data["task_id"]))
    assert task is not None
    assert str(task.organization_id) == org["id"]

    analysis = await db_session.get(Analysis, UUID(data["analysis_id"]))
    assert analysis is not None
    assert str(analysis.organization_id) == org["id"]

    audits = await db_session.execute(
        select(AuditEvent).where(AuditEvent.action == "log_analysis.async.created")
    )
    event = audits.scalar_one()
    assert event.organization_id is not None
    assert str(event.organization_id) == org["id"]
    assert "log_bytes" in (event.metadata_json or {})
    assert "CrashLoop" not in str(event.metadata_json)


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["admin", "member"])
async def test_organization_async_log_analysis_as_admin_or_member(
    client: AsyncClient, role: str
) -> None:
    owner_headers = await _register_login(
        client, email=f"owner-{role}@example.com", username=f"owner{role}"
    )
    member_headers = await _register_login(
        client, email=f"{role}@example.com", username=role
    )
    org = await _create_org(client, owner_headers)
    add = await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        headers=owner_headers,
        json={"email": f"{role}@example.com", "role": role},
    )
    assert add.status_code == 200, add.text

    response = await client.post(
        "/api/v1/logs/analyze/async",
        headers=member_headers,
        json={
            "content": "permission denied\n",
            "provider": "gemini",
            "organization_id": org["id"],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["organization_id"] == org["id"]


@pytest.mark.asyncio
async def test_viewer_denied_organization_async_log_analysis(
    client: AsyncClient,
) -> None:
    owner_headers = await _register_login(
        client, email="view-owner@example.com", username="viewowner"
    )
    viewer_headers = await _register_login(
        client, email="viewer@example.com", username="logviewer"
    )
    org = await _create_org(client, owner_headers)
    add = await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        headers=owner_headers,
        json={"email": "viewer@example.com", "role": "viewer"},
    )
    assert add.status_code == 200, add.text

    denied = await client.post(
        "/api/v1/logs/analyze/async",
        headers=viewer_headers,
        json={
            "content": "CrashLoopBackOff\n",
            "provider": "gemini",
            "organization_id": org["id"],
        },
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_non_member_denied_unknown_organization_style(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    owner_headers = await _register_login(
        client, email="secret-owner@example.com", username="secretowner"
    )
    org = await _create_org(client, owner_headers)

    denied = await client.post(
        "/api/v1/logs/analyze/async",
        headers=auth_headers,
        json={
            "content": "CrashLoopBackOff\n",
            "provider": "gemini",
            "organization_id": org["id"],
        },
    )
    assert denied.status_code == 404


@pytest.mark.asyncio
async def test_invalid_organization_uuid_validation(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/logs/analyze/async",
        headers=auth_headers,
        json={
            "content": "CrashLoopBackOff\n",
            "provider": "gemini",
            "organization_id": "not-a-uuid",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unknown_organization_not_found(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/logs/analyze/async",
        headers=auth_headers,
        json={
            "content": "CrashLoopBackOff\n",
            "provider": "gemini",
            "organization_id": str(uuid4()),
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cross_organization_task_access_denied(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    org = await _create_org(client, auth_headers)
    created = await client.post(
        "/api/v1/logs/analyze/async",
        headers=auth_headers,
        json={
            "content": "CrashLoopBackOff\n",
            "provider": "gemini",
            "organization_id": org["id"],
        },
    )
    task_id = created.json()["data"]["task_id"]

    outsider = await _register_login(
        client, email="outsider@example.com", username="outsider"
    )
    denied = await client.get(f"/api/v1/tasks/{task_id}", headers=outsider)
    assert denied.status_code == 404


@pytest.mark.asyncio
async def test_worker_derives_organization_scope_from_task_record(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from contextlib import asynccontextmanager

    from app.workers import tasks as worker_tasks

    org = await _create_org(client, auth_headers)
    me = await client.get("/api/v1/users/me", headers=auth_headers)
    user_id = me.json()["data"]["id"]
    created = await client.post(
        "/api/v1/logs/analyze/async",
        headers=auth_headers,
        json={
            "content": "CrashLoopBackOff\nERROR: Job failed\n",
            "provider": "gemini",
            "organization_id": org["id"],
        },
    )
    assert created.status_code == 200, created.text
    data = created.json()["data"]

    @asynccontextmanager
    async def _session_cm():
        yield db_session

    monkeypatch.setattr(worker_tasks, "AsyncSessionLocal", _session_cm)

    result = await worker_tasks._analyze_logs_async(
        data["task_id"],
        data["analysis_id"],
        user_id,
        "CrashLoopBackOff\nERROR: Job failed\n",
        "gemini",
    )
    assert result.get("summary") or result.get("error")

    await db_session.refresh(await db_session.get(Analysis, UUID(data["analysis_id"])))
    analysis = await db_session.get(Analysis, UUID(data["analysis_id"]))
    assert analysis is not None
    assert str(analysis.organization_id) == org["id"]


@pytest.mark.asyncio
async def test_celery_delay_does_not_receive_organization_id_argument(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def _delay(*args: Any, **kwargs: Any) -> Any:
        captured["args"] = args
        captured["kwargs"] = kwargs

        class AsyncResult:
            id = f"celery-{uuid4().hex[:12]}"

        return AsyncResult()

    from app.workers import tasks as worker_tasks

    monkeypatch.setattr(worker_tasks.analyze_logs_task, "delay", _delay)

    org = await _create_org(client, auth_headers)
    response = await client.post(
        "/api/v1/logs/analyze/async",
        headers=auth_headers,
        json={
            "content": "CrashLoopBackOff\n",
            "provider": "gemini",
            "organization_id": org["id"],
        },
    )
    assert response.status_code == 200, response.text
    assert "organization_id" not in captured.get("kwargs", {})
    # positional: background_task_id, analysis_id, user_id, content, provider
    assert len(captured["args"]) == 5
