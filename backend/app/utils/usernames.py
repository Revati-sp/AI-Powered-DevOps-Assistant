from __future__ import annotations

import re
from urllib.parse import urlparse
from zoneinfo import available_timezones

from app.core.exceptions import ValidationAppError

RESERVED_USERNAMES = frozenset(
    {
        "admin",
        "administrator",
        "api",
        "auth",
        "devops",
        "me",
        "null",
        "root",
        "support",
        "system",
        "undefined",
    }
)
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")


def normalize_username(value: str) -> str:
    return value.strip().lower()


def normalize_display_name(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    return normalized or None


def validate_username(value: str) -> str:
    username = normalize_username(value)
    if not 3 <= len(username) <= 100:
        raise ValidationAppError("Username must be between 3 and 100 characters.")
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValidationAppError(
            "Username may contain only letters, numbers, periods, hyphens, and underscores."
        )
    if username in RESERVED_USERNAMES:
        raise ValidationAppError("This username is reserved.")
    return username


def validate_timezone(value: str | None) -> str | None:
    if value is None:
        return None
    timezone = value.strip()
    if not timezone:
        return None
    if timezone not in available_timezones():
        raise ValidationAppError("Timezone must be a valid IANA timezone name.")
    return timezone


def validate_avatar_url(value: str | None) -> str | None:
    if value is None:
        return None
    avatar_url = value.strip()
    if not avatar_url:
        return None
    if len(avatar_url) > 512:
        raise ValidationAppError("Avatar URL must be at most 512 characters.")
    parsed = urlparse(avatar_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationAppError("Avatar URL must use http or https.")
    return avatar_url
