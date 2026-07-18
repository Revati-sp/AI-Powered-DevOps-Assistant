import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

SENSITIVE_KEYS = {
    "password",
    "hashed_password",
    "secret",
    "secret_key",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "gemini_api_key",
    "authorization",
    "cookie",
    "cookies",
    "database_url",
    "smtp_password",
}


def redact_secrets(data: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            redacted[key] = "***REDACTED***"
        elif isinstance(value, dict):
            redacted[key] = redact_secrets(value)
        else:
            redacted[key] = value
    return redacted


class JsonLogFormatter(logging.Formatter):
    def __init__(self, *, service: str, environment: str) -> None:
        super().__init__()
        self.service = service
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", self.service),
            "environment": getattr(record, "environment", self.environment),
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "request_id",
            "trace_id",
            "route",
            "status",
            "duration",
            "error_category",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["error_category"] = payload.get("error_category") or "exception"
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging(
    debug: bool = False,
    *,
    log_format: str = "text",
    service: str = "api",
    environment: str = "development",
) -> None:
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        handler.setFormatter(JsonLogFormatter(service=service, environment=environment))
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
    logging.basicConfig(level=level, handlers=[handler], force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
