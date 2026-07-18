from __future__ import annotations

import json
from typing import Any


def encode_sse(event: str, data: dict[str, Any]) -> str:
    """Encode a named Server-Sent Event with a JSON data payload."""
    payload = json.dumps(data, separators=(",", ":"), default=str)
    return f"event: {event}\ndata: {payload}\n\n"
