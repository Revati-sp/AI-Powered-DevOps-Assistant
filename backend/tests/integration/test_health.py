from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_ready_with_mocked_deps(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeConn:
        async def execute(self, *_args, **_kwargs):  # noqa: ANN001
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

    class FakeEngine:
        def connect(self):
            return FakeConn()

    fake_redis = MagicMock()
    fake_redis.ping = AsyncMock(return_value=True)
    fake_redis.aclose = AsyncMock()

    monkeypatch.setattr("app.api.routes.health.engine", FakeEngine())
    monkeypatch.setattr(
        "app.api.routes.health.redis_from_url",
        lambda *_args, **_kwargs: fake_redis,
    )

    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json()["data"]["database"] == "ok"
    assert response.json()["data"]["redis"] == "ok"
