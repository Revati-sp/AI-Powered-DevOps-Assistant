from __future__ import annotations

from typing import Literal

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status_class"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route", "status_class"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
LLM_REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total LLM requests",
    ["provider", "operation", "result"],
)
LLM_REQUEST_DURATION_SECONDS = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["provider", "operation"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)
LLM_ERRORS_TOTAL = Counter(
    "llm_errors_total",
    "Total LLM errors",
    ["provider", "operation"],
)
RATE_LIMIT_REJECTIONS_TOTAL = Counter(
    "rate_limit_rejections_total",
    "Total rate limit rejections",
    ["category"],
)
BACKGROUND_TASKS_TOTAL = Counter(
    "background_tasks_total",
    "Total background task events",
    ["task_type", "result"],
)
BACKGROUND_TASK_DURATION_SECONDS = Histogram(
    "background_task_duration_seconds",
    "Background task duration in seconds",
    ["task_type"],
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)
POLICY_VIOLATIONS_TOTAL = Counter(
    "policy_violations_total",
    "Total organization policy violations",
    ["severity", "artifact_type"],
)
ARTIFACT_VERSIONS_CREATED_TOTAL = Counter(
    "artifact_versions_created_total",
    "Total artifact versions created",
    ["artifact_type"],
)
ORGANIZATION_OPERATIONS_TOTAL = Counter(
    "organization_operations_total",
    "Total organization operations",
    ["operation", "role"],
)


def status_class(status_code: int) -> str:
    return f"{status_code // 100}xx"


def record_http_request(
    *,
    method: str,
    route: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    status = status_class(status_code)
    HTTP_REQUESTS_TOTAL.labels(method=method, route=route, status_class=status).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method, route=route, status_class=status
    ).observe(duration_seconds)


def record_llm_request(
    *,
    provider: str,
    operation: str,
    duration_seconds: float,
    success: bool,
) -> None:
    result: Literal["success", "error"] = "success" if success else "error"
    LLM_REQUESTS_TOTAL.labels(
        provider=provider, operation=operation, result=result
    ).inc()
    LLM_REQUEST_DURATION_SECONDS.labels(provider=provider, operation=operation).observe(
        duration_seconds
    )
    if not success:
        LLM_ERRORS_TOTAL.labels(provider=provider, operation=operation).inc()


def record_rate_limit_rejection(category: str) -> None:
    RATE_LIMIT_REJECTIONS_TOTAL.labels(category=category).inc()


def record_background_task(task_type: str, result: str) -> None:
    BACKGROUND_TASKS_TOTAL.labels(task_type=task_type, result=result).inc()


def record_background_task_duration(task_type: str, duration_seconds: float) -> None:
    BACKGROUND_TASK_DURATION_SECONDS.labels(task_type=task_type).observe(
        duration_seconds
    )


def record_policy_violation(severity: str, artifact_type: str) -> None:
    POLICY_VIOLATIONS_TOTAL.labels(severity=severity, artifact_type=artifact_type).inc()


def record_artifact_version_created(artifact_type: str) -> None:
    ARTIFACT_VERSIONS_CREATED_TOTAL.labels(artifact_type=artifact_type).inc()


def record_organization_operation(operation: str, role: str) -> None:
    ORGANIZATION_OPERATIONS_TOTAL.labels(operation=operation, role=role).inc()


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST


def reset_metrics_for_tests() -> None:
    collectors = [
        HTTP_REQUESTS_TOTAL,
        HTTP_REQUEST_DURATION_SECONDS,
        LLM_REQUESTS_TOTAL,
        LLM_REQUEST_DURATION_SECONDS,
        LLM_ERRORS_TOTAL,
        RATE_LIMIT_REJECTIONS_TOTAL,
        BACKGROUND_TASKS_TOTAL,
        BACKGROUND_TASK_DURATION_SECONDS,
        POLICY_VIOLATIONS_TOTAL,
        ARTIFACT_VERSIONS_CREATED_TOTAL,
        ORGANIZATION_OPERATIONS_TOTAL,
    ]
    for collector in collectors:
        collector._metrics.clear()
