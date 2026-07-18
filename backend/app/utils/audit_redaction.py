from __future__ import annotations

import re
from typing import Any

_REDACT_KEY_PATTERN = re.compile(
    r"(password|secret|token|api[_-]?key|authorization|cookie|credential|"
    r"private[_-]?key|prompt|content|log|file|access_token|refresh_token)",
    re.IGNORECASE,
)

_REDACT_VALUE_PATTERN = re.compile(
    r"(?i)(password|secret|api[_-]?key|token|authorization|bearer\s+\S+|"
    r"-----BEGIN\s+[A-Z\s]+PRIVATE KEY-----)",
)


def _should_redact_key(key: str) -> bool:
    return bool(_REDACT_KEY_PATTERN.search(key))


def redact_metadata(value: Any, *, _depth: int = 0) -> Any:
    """Recursively redact sensitive keys and values from audit metadata."""
    if _depth > 20:
        return "[TRUNCATED]"

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if _should_redact_key(str(key)):
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = redact_metadata(item, _depth=_depth + 1)
        return redacted

    if isinstance(value, list):
        return [redact_metadata(item, _depth=_depth + 1) for item in value]

    if isinstance(value, tuple):
        return [redact_metadata(item, _depth=_depth + 1) for item in value]

    if isinstance(value, str):
        if _REDACT_VALUE_PATTERN.search(value):
            return "[REDACTED]"
        if len(value) > 500:
            return f"[TRUNCATED:{len(value)} chars]"
        return value

    return value
