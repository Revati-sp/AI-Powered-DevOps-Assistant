from __future__ import annotations

import pytest
from app.core.config import get_settings
from app.services.provider_circuit_breaker import CircuitState, ProviderCircuitBreaker


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures() -> None:
    settings = get_settings()
    breaker = ProviderCircuitBreaker(settings=settings)
    breaker.settings.provider_circuit_failure_threshold = 2
    breaker.settings.provider_circuit_recovery_seconds = 60

    await breaker.record_failure("gemini", category="transient")
    assert (await breaker.get_state("gemini")).state == CircuitState.CLOSED

    await breaker.record_failure("gemini", category="transient")
    assert (await breaker.get_state("gemini")).state == CircuitState.OPEN
    assert await breaker.is_open("gemini") is True


@pytest.mark.asyncio
async def test_circuit_breaker_records_success_latency() -> None:
    breaker = ProviderCircuitBreaker()
    await breaker.record_success("mistral", 120.0)
    snapshot = await breaker.get_state("mistral")
    assert snapshot.state == CircuitState.CLOSED
    assert snapshot.avg_latency_ms == pytest.approx(120.0)
