from __future__ import annotations

import enum
import json
import time
from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis
from redis.asyncio import from_url as redis_from_url

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CircuitState(str, enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True)
class CircuitSnapshot:
    provider_name: str
    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_category: str | None
    last_success_at: float | None
    avg_latency_ms: float | None


class ProviderCircuitBreaker:
    def __init__(
        self,
        redis_client: Redis | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._redis = redis_client
        self._owns_redis = redis_client is None
        self._memory: dict[str, dict[str, Any]] = {}

    def _key(self, provider_name: str) -> str:
        return f"{self.settings.provider_circuit_redis_prefix}:{provider_name}"

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = redis_from_url(
                self.settings.redis_url, encoding="utf-8", decode_responses=True
            )
        return self._redis

    async def get_state(self, provider_name: str) -> CircuitSnapshot:
        try:
            client = await self._get_redis()
            raw = await client.get(self._key(provider_name))
            if raw:
                data = json.loads(raw)
                return self._snapshot_from_data(provider_name, data)
        except Exception:  # noqa: BLE001
            logger.debug("Circuit breaker falling back to memory for %s", provider_name)
        data = self._memory.get(provider_name, {})
        return self._snapshot_from_data(provider_name, data)

    def _snapshot_from_data(
        self, provider_name: str, data: dict[str, Any]
    ) -> CircuitSnapshot:
        state_raw = str(data.get("state", CircuitState.CLOSED.value))
        try:
            state = CircuitState(state_raw)
        except ValueError:
            state = CircuitState.CLOSED
        latencies = data.get("latencies_ms") or []
        avg = None
        if latencies:
            avg = sum(float(v) for v in latencies[-20:]) / min(len(latencies), 20)
        return CircuitSnapshot(
            provider_name=provider_name,
            state=state,
            failure_count=int(data.get("failure_count", 0)),
            success_count=int(data.get("success_count", 0)),
            last_failure_category=data.get("last_failure_category"),
            last_success_at=data.get("last_success_at"),
            avg_latency_ms=avg,
        )

    async def is_open(self, provider_name: str) -> bool:
        snapshot = await self.get_state(provider_name)
        if snapshot.state != CircuitState.OPEN:
            return False
        data = await self._load(provider_name)
        opened_at = float(data.get("opened_at") or 0)
        if opened_at and (
            time.time() - opened_at >= self.settings.provider_circuit_recovery_seconds
        ):
            await self._save(
                provider_name,
                {
                    **data,
                    "state": CircuitState.HALF_OPEN.value,
                },
            )
            return False
        return True

    async def record_success(self, provider_name: str, latency_ms: float) -> None:
        data = await self._load(provider_name)
        latencies = list(data.get("latencies_ms") or [])
        latencies.append(latency_ms)
        latencies = latencies[-20:]
        await self._save(
            provider_name,
            {
                **data,
                "state": CircuitState.CLOSED.value,
                "failure_count": 0,
                "success_count": int(data.get("success_count", 0)) + 1,
                "last_success_at": time.time(),
                "latencies_ms": latencies,
            },
        )

    async def record_failure(
        self, provider_name: str, *, category: str = "transient"
    ) -> None:
        data = await self._load(provider_name)
        failures = int(data.get("failure_count", 0)) + 1
        state = CircuitState.CLOSED.value
        opened_at = data.get("opened_at")
        if failures >= self.settings.provider_circuit_failure_threshold:
            state = CircuitState.OPEN.value
            opened_at = time.time()
        await self._save(
            provider_name,
            {
                **data,
                "state": state,
                "failure_count": failures,
                "last_failure_category": category,
                "opened_at": opened_at,
            },
        )

    async def _load(self, provider_name: str) -> dict[str, Any]:
        try:
            client = await self._get_redis()
            raw = await client.get(self._key(provider_name))
            if raw:
                loaded = json.loads(raw)
                if isinstance(loaded, dict):
                    return loaded
        except Exception:  # noqa: BLE001
            pass
        return dict(self._memory.get(provider_name, {}))

    async def _save(self, provider_name: str, data: dict[str, Any]) -> None:
        self._memory[provider_name] = data
        try:
            client = await self._get_redis()
            await client.set(
                self._key(provider_name),
                json.dumps(data),
                ex=self.settings.provider_circuit_state_ttl_seconds,
            )
        except Exception:  # noqa: BLE001
            logger.debug("Circuit breaker Redis write failed for %s", provider_name)

    async def aclose(self) -> None:
        if self._owns_redis and self._redis is not None:
            await self._redis.aclose()


_circuit_breaker: ProviderCircuitBreaker | None = None


def get_circuit_breaker() -> ProviderCircuitBreaker:
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = ProviderCircuitBreaker()
    return _circuit_breaker


def set_circuit_breaker(breaker: ProviderCircuitBreaker | None) -> None:
    global _circuit_breaker
    _circuit_breaker = breaker
