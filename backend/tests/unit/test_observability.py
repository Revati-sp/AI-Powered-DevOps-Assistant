from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
from app.core.config import Settings, get_settings
from app.core.metrics import (
    HTTP_REQUESTS_TOTAL,
    reset_metrics_for_tests,
)
from app.core.observability import (
    RequestIdFilter,
    get_trace_context,
    init_observability,
    shutdown_observability,
)
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def reset_observability_state() -> None:
    shutdown_observability()
    reset_metrics_for_tests()
    get_settings.cache_clear()
    yield
    shutdown_observability()
    reset_metrics_for_tests()


def test_observability_disabled_without_exporter() -> None:
    init_observability(get_settings())
    init_observability(get_settings())
    shutdown_observability()


@pytest.mark.asyncio
async def test_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "req-test-123"})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "req-test-123"


@pytest.mark.asyncio
async def test_request_id_generated_when_missing(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


@pytest.mark.asyncio
async def test_metrics_endpoint_enabled(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


@pytest.mark.asyncio
async def test_metrics_disabled_returns_404(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("METRICS_ENABLED", "false")
    get_settings.cache_clear()
    response = await client.get("/metrics")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_http_metrics_use_low_cardinality_labels(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.get("/health")
    await client.get("/api/v1/users/me", headers=auth_headers)
    labels = HTTP_REQUESTS_TOTAL._metrics.keys()  # type: ignore[attr-defined]
    for label_values in labels:
        label_map = dict(
            zip(HTTP_REQUESTS_TOTAL._labelnames, label_values, strict=True)
        )
        for value in label_map.values():
            assert "@" not in value
            assert len(value) < 100


def test_metrics_labels_do_not_include_uuid_values() -> None:
    from app.core.metrics import record_background_task, record_llm_request

    record_background_task("log_analysis", "succeeded")
    record_llm_request(
        provider="gemini",
        operation="generate",
        duration_seconds=0.1,
        success=True,
    )
    sample = str(HTTP_REQUESTS_TOTAL.collect()[0].samples)
    assert "dev@" not in sample


@pytest.mark.asyncio
async def test_metrics_require_auth(
    client: AsyncClient,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("METRICS_REQUIRE_AUTH", "true")
    get_settings.cache_clear()

    denied = await client.get("/metrics")
    assert denied.status_code == 401
    allowed = await client.get("/metrics", headers=auth_headers)
    assert allowed.status_code == 200


def test_init_observability_with_otel_enabled_no_exporter(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_ENABLED", "true")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    get_settings.cache_clear()
    settings = get_settings()

    mock_provider = MagicMock()
    with (
        patch("opentelemetry.sdk.trace.TracerProvider", return_value=mock_provider),
        patch("opentelemetry.trace.set_tracer_provider") as set_provider,
        patch("opentelemetry.sdk.resources.Resource.create"),
        patch("opentelemetry.sdk.trace.sampling.TraceIdRatioBased"),
    ):
        init_observability(settings)
        set_provider.assert_called_once_with(mock_provider)

    shutdown_observability()
    mock_provider.shutdown.assert_called_once()


def test_init_observability_with_otlp_exporter(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_ENABLED", "true")
    monkeypatch.setenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318/v1/traces"
    )
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", "Authorization=Bearer test-token")
    get_settings.cache_clear()
    settings = get_settings()

    mock_provider = MagicMock()
    mock_exporter = MagicMock()
    with (
        patch("opentelemetry.sdk.trace.TracerProvider", return_value=mock_provider),
        patch("opentelemetry.trace.set_tracer_provider"),
        patch("opentelemetry.sdk.resources.Resource.create"),
        patch("opentelemetry.sdk.trace.sampling.TraceIdRatioBased"),
        patch(
            "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter",
            return_value=mock_exporter,
        ) as exporter_cls,
        patch("opentelemetry.sdk.trace.export.BatchSpanProcessor") as processor_cls,
    ):
        init_observability(settings)
        exporter_cls.assert_called_once()
        processor_cls.assert_called_once()
        mock_provider.add_span_processor.assert_called_once()

    shutdown_observability()


def test_init_observability_is_idempotent(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_ENABLED", "true")
    get_settings.cache_clear()
    settings = get_settings()

    mock_provider = MagicMock()
    with (
        patch("opentelemetry.sdk.trace.TracerProvider", return_value=mock_provider),
        patch("opentelemetry.trace.set_tracer_provider") as set_provider,
        patch("opentelemetry.sdk.resources.Resource.create"),
        patch("opentelemetry.sdk.trace.sampling.TraceIdRatioBased"),
    ):
        init_observability(settings)
        init_observability(settings)
        set_provider.assert_called_once()

    shutdown_observability()


def test_shutdown_observability_handles_provider_errors() -> None:
    import app.core.observability as observability_module

    mock_provider = MagicMock()
    mock_provider.shutdown.side_effect = RuntimeError("shutdown failed")
    observability_module._tracer_provider = mock_provider
    observability_module._initialized = True

    shutdown_observability()
    assert observability_module._tracer_provider is None
    assert observability_module._initialized is False


def test_get_trace_context_when_disabled() -> None:
    assert get_trace_context() == {}


def test_get_trace_context_with_valid_span(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_ENABLED", "true")
    monkeypatch.setenv("OTEL_LOG_CORRELATION", "true")
    get_settings.cache_clear()

    mock_context = MagicMock()
    mock_context.is_valid = True
    mock_context.trace_id = 1
    mock_context.span_id = 2
    mock_span = MagicMock()
    mock_span.get_span_context.return_value = mock_context

    with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
        ctx = get_trace_context()

    assert ctx["trace_id"] == format(1, "032x")
    assert ctx["span_id"] == format(2, "016x")


def test_request_id_filter_attaches_trace_fields(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_ENABLED", "true")
    monkeypatch.setenv("OTEL_LOG_CORRELATION", "true")
    get_settings.cache_clear()

    mock_context = MagicMock()
    mock_context.is_valid = True
    mock_context.trace_id = 9
    mock_context.span_id = 8
    mock_span = MagicMock()
    mock_span.get_span_context.return_value = mock_context

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    filt = RequestIdFilter(request_id="req-abc")

    with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
        assert filt.filter(record) is True

    assert record.request_id == "req-abc"
    assert record.trace_id == format(9, "032x")
    assert record.span_id == format(8, "016x")


def test_init_observability_handles_import_failure(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_ENABLED", "true")
    get_settings.cache_clear()
    settings = Settings(
        app_env="test",
        secret_key="test-secret-key-123456",
        otel_enabled=True,
    )

    with patch(
        "opentelemetry.sdk.trace.TracerProvider",
        side_effect=ImportError("missing otel"),
    ):
        init_observability(settings)

    shutdown_observability()
