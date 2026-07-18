from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
_initialized = False
_tracer_provider: Any | None = None


def init_observability(
    settings: Settings | None = None,
    *,
    app: FastAPI | None = None,
) -> None:
    global _initialized, _tracer_provider
    if _initialized:
        return

    cfg = settings or get_settings()
    if not cfg.otel_enabled:
        _initialized = True
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

        resource = Resource.create({"service.name": cfg.otel_service_name})
        sampler = TraceIdRatioBased(max(0.0, min(1.0, cfg.otel_traces_sample_ratio)))
        provider = TracerProvider(resource=resource, sampler=sampler)

        if cfg.otel_exporter_otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            headers = _parse_otlp_headers(cfg.otel_exporter_otlp_headers)
            exporter = OTLPSpanExporter(
                endpoint=cfg.otel_exporter_otlp_endpoint,
                headers=headers,
                timeout=cfg.otel_export_timeout_seconds,
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)
        _tracer_provider = provider

        _instrument_libraries(cfg, app=app)
        _initialized = True
        logger.info("OpenTelemetry initialized for %s", cfg.otel_service_name)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "OpenTelemetry initialization failed: %s", exc.__class__.__name__
        )
        _initialized = True


def shutdown_observability() -> None:
    global _initialized, _tracer_provider
    if _tracer_provider is not None:
        try:
            _tracer_provider.shutdown()
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenTelemetry shutdown failed: %s", exc.__class__.__name__)
    _tracer_provider = None
    _initialized = False


def get_trace_context() -> dict[str, str]:
    cfg = get_settings()
    if not cfg.otel_enabled or not cfg.otel_log_correlation:
        return {}
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        context = span.get_span_context()
        if not context.is_valid:
            return {}
        return {
            "trace_id": format(context.trace_id, "032x"),
            "span_id": format(context.span_id, "016x"),
        }
    except Exception:  # noqa: BLE001
        return {}


def _parse_otlp_headers(raw: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for part in raw.split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            headers[key] = value
    return headers


def _instrument_libraries(cfg: Settings, *, app: FastAPI | None = None) -> None:
    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
        except Exception as exc:  # noqa: BLE001
            logger.debug("FastAPI instrumentation skipped: %s", exc)

    for instrumentor_path in (
        "opentelemetry.instrumentation.httpx.HTTPXClientInstrumentor",
        "opentelemetry.instrumentation.sqlalchemy.SQLAlchemyInstrumentor",
        "opentelemetry.instrumentation.redis.RedisInstrumentor",
        "opentelemetry.instrumentation.celery.CeleryInstrumentor",
    ):
        try:
            module_name, class_name = instrumentor_path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            instrumentor = getattr(module, class_name)()
            if class_name == "SQLAlchemyInstrumentor":
                from app.core.database import engine

                instrumentor.instrument(engine=engine.sync_engine)
            else:
                instrumentor.instrument()
        except Exception as exc:  # noqa: BLE001
            logger.debug("%s skipped: %s", instrumentor_path, exc)


class RequestIdFilter(logging.Filter):
    def __init__(self, request_id: str = "") -> None:
        super().__init__()
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(record, "request_id", self.request_id)
        trace_context = get_trace_context()
        record.trace_id = trace_context.get("trace_id", "")
        record.span_id = trace_context.get("span_id", "")
        return True
