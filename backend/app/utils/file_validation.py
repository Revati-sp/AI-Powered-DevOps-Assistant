from pathlib import PurePath

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.utils.filename import sanitize_filename

ALLOWED_LOG_EXTENSIONS = {".log", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "application/octet-stream",
    "text/x-log",
}
_TEXT_CONTROL_CHARS = {9, 10, 13}  # tab, LF, CR
_PRINTABLE_ASCII = set(range(0x20, 0x7F))


def _looks_binary(data: bytes) -> bool:
    if not data:
        return False
    sample = data[:8192]
    disallowed = sum(
        1
        for byte in sample
        if byte not in _PRINTABLE_ASCII and byte not in _TEXT_CONTROL_CHARS
    )
    return disallowed / len(sample) > 0.30


async def read_and_validate_upload(file: UploadFile) -> str:
    settings = get_settings()
    raw_filename = file.filename or ""
    if len(raw_filename) > settings.max_filename_length:
        raise ValidationAppError(
            "Filename exceeds maximum allowed length.",
            details={"max_filename_length": settings.max_filename_length},
        )

    filename = sanitize_filename(raw_filename, max_length=settings.max_filename_length)
    suffix = PurePath(filename).suffix.lower()

    if suffix not in ALLOWED_LOG_EXTENSIONS:
        raise ValidationAppError(
            "Unsupported file type. Only .log and .txt files are allowed.",
            details={"filename": filename},
        )

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationAppError(
            "Unsupported content type for upload.",
            details={"content_type": file.content_type},
        )

    data = await file.read()
    if not data:
        raise ValidationAppError("Uploaded file is empty.")

    max_bytes = min(settings.max_upload_size_bytes, settings.max_log_text_size_bytes)
    if len(data) > max_bytes:
        raise ValidationAppError(
            f"File exceeds maximum size of {settings.max_upload_size_mb} MB.",
            details={"size_bytes": len(data), "max_bytes": max_bytes},
        )

    if b"\x00" in data:
        raise ValidationAppError("Uploaded file must not contain null bytes.")

    if _looks_binary(data):
        raise ValidationAppError("Uploaded file appears to be binary, not text.")

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationAppError("Uploaded file must be valid UTF-8 text.") from exc

    line_count = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    if line_count > settings.max_log_lines:
        raise ValidationAppError(
            "Uploaded file exceeds maximum line count.",
            details={
                "line_count": line_count,
                "max_log_lines": settings.max_log_lines,
            },
        )

    return text
