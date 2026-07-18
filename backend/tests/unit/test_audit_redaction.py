from __future__ import annotations

from app.utils.audit_redaction import redact_metadata


def test_redacts_sensitive_keys() -> None:
    payload = {
        "username": "devops",
        "password": "secret123",
        "metadata": {"api_key": "abc", "safe": "ok"},
    }
    redacted = redact_metadata(payload)
    assert redacted["password"] == "[REDACTED]"
    assert redacted["metadata"]["api_key"] == "[REDACTED]"
    assert redacted["metadata"]["safe"] == "ok"


def test_redacts_prompt_and_content_values() -> None:
    payload = {
        "prompt": "Analyze this cluster failure with token=abc123",
        "artifact": {"content": "apiVersion: v1\nkind: Pod\n"},
    }
    redacted = redact_metadata(payload)
    assert redacted["prompt"] == "[REDACTED]"
    assert redacted["artifact"]["content"] == "[REDACTED]"


def test_truncates_long_strings() -> None:
    payload = {"note": "x" * 600}
    redacted = redact_metadata(payload)
    assert redacted["note"].startswith("[TRUNCATED:")


def test_redacts_nested_lists() -> None:
    payload = {"entries": [{"access_token": "jwt-value"}]}
    redacted = redact_metadata(payload)
    assert redacted["entries"][0]["access_token"] == "[REDACTED]"
