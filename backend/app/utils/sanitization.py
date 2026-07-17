import re

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[^\s'\"]+"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*"),
]


def sanitize_text(value: str, *, max_length: int | None = None) -> str:
    cleaned = CONTROL_CHARS.sub("", value).replace("\r\n", "\n").strip()
    if max_length is not None:
        cleaned = cleaned[:max_length]
    return cleaned


def redact_secrets_in_text(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(r"\1=***REDACTED***", redacted)
    return redacted


def preview_text(value: str, limit: int = 500) -> str:
    sanitized = sanitize_text(value)
    if len(sanitized) <= limit:
        return sanitized
    return f"{sanitized[:limit]}..."
