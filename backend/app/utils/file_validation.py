from pathlib import PurePath

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError

ALLOWED_LOG_EXTENSIONS = {".log", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "application/octet-stream",
    "text/x-log",
}


async def read_and_validate_upload(file: UploadFile) -> str:
    settings = get_settings()
    filename = file.filename or ""
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
    if len(data) > settings.max_upload_size_bytes:
        raise ValidationAppError(
            f"File exceeds maximum size of {settings.max_upload_size_mb} MB.",
            details={"size_bytes": len(data)},
        )

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationAppError("Uploaded file must be valid UTF-8 text.") from exc
