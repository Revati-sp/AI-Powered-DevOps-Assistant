from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from app.models.background_task import TaskStatus
from app.services.task_service import TASK_TYPE_LOG_ANALYSIS, TaskService
from app.workers.celery_app import celery_app
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def mock_celery_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    celery_app.conf.task_always_eager = False

    def _delay(*args: Any, **kwargs: Any) -> Any:
        class AsyncResult:
            id = f"celery-{uuid4().hex[:12]}"

        return AsyncResult()

    from app.workers import tasks as worker_tasks

    monkeypatch.setattr(worker_tasks.analyze_logs_task, "delay", _delay)


@pytest.mark.asyncio
async def test_async_log_analysis_creates_background_task(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/logs/analyze/async",
        headers={**auth_headers, "Idempotency-Key": "log-analyze-1"},
        json={"content": "CrashLoopBackOff\nERROR: Job failed\n", "provider": "gemini"},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["status"] in {"queued", "running", "succeeded"}
    assert data["task_id"]
    assert data["analysis_id"] is not None


@pytest.mark.asyncio
async def test_idempotent_async_log_analysis(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    payload = {
        "content": "CrashLoopBackOff\nERROR: duplicate test\n",
        "provider": "gemini",
    }
    headers = {**auth_headers, "Idempotency-Key": "duplicate-log-task"}
    first = await client.post(
        "/api/v1/logs/analyze/async",
        headers=headers,
        json=payload,
    )
    second = await client.post(
        "/api/v1/logs/analyze/async",
        headers=headers,
        json=payload,
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["task_id"] == second.json()["data"]["task_id"]
    assert first.json()["data"]["analysis_id"] == second.json()["data"]["analysis_id"]


@pytest.mark.asyncio
async def test_task_list_get_and_cancel(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create = await client.post(
        "/api/v1/logs/analyze/async",
        headers=auth_headers,
        json={"content": "CrashLoopBackOff\n", "provider": "gemini"},
    )
    task_id = create.json()["data"]["task_id"]

    listed = await client.get("/api/v1/tasks", headers=auth_headers)
    assert listed.status_code == 200
    items = listed.json()["data"]["items"]
    assert any(item["id"] == task_id for item in items)

    detail = await client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == task_id

    cancel = await client.post(
        f"/api/v1/tasks/{task_id}/cancel",
        headers=auth_headers,
    )
    assert cancel.status_code == 200
    assert cancel.json()["data"]["status"] in {
        TaskStatus.CANCELLED.value,
        TaskStatus.SUCCEEDED.value,
        TaskStatus.FAILED.value,
        TaskStatus.QUEUED.value,
        TaskStatus.RUNNING.value,
    }

    cancel_again = await client.post(
        f"/api/v1/tasks/{task_id}/cancel",
        headers=auth_headers,
    )
    assert cancel_again.status_code == 200


@pytest.mark.asyncio
async def test_legacy_task_status_route(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create = await client.post(
        "/api/v1/logs/analyze/async",
        headers=auth_headers,
        json={"content": "CrashLoopBackOff\n", "provider": "gemini"},
    )
    task_id = create.json()["data"]["task_id"]
    status = await client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert status.status_code == 200
    body = status.json()["data"]
    assert str(body["task_id"]) == task_id
    assert "status" in body


@pytest.mark.asyncio
async def test_task_cleanup_helper(db_session) -> None:
    service = TaskService(db_session)
    deleted = await service.cleanup_expired_tasks()
    assert deleted >= 0


@pytest.mark.asyncio
async def test_cross_user_task_access_denied(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create = await client.post(
        "/api/v1/logs/analyze/async",
        headers=auth_headers,
        json={"content": "CrashLoopBackOff\n", "provider": "gemini"},
    )
    task_id = create.json()["data"]["task_id"]

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

    denied = await client.get(f"/api/v1/tasks/{task_id}", headers=other_headers)
    assert denied.status_code == 404


@pytest.mark.asyncio
async def test_task_service_lifecycle(db_session, fake_llm) -> None:
    from uuid import uuid4

    from app.models.user import User, UserRole

    user = User(
        id=uuid4(),
        email="task-user@example.com",
        username="taskuser",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    service = TaskService(db_session)
    task = await service.create_task(user, task_type=TASK_TYPE_LOG_ANALYSIS)
    await service.mark_running(task.id, progress=25)
    await service.mark_succeeded(task.id, {"analysis_id": str(uuid4())})
    detail = await service.get_task(user, task.id)
    assert detail.status == TaskStatus.SUCCEEDED
    assert detail.progress == 100
