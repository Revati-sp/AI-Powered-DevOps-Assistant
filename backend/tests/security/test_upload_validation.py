from io import BytesIO

import pytest
from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.utils.file_validation import read_and_validate_upload
from fastapi import UploadFile


def _upload(
    *,
    filename: str = "app.log",
    content: bytes = b"line one\nline two\n",
    content_type: str = "text/plain",
) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers={"content-type": content_type},
    )


@pytest.mark.asyncio
async def test_rejects_empty_upload() -> None:
    with pytest.raises(ValidationAppError, match="empty"):
        await read_and_validate_upload(_upload(content=b""))


@pytest.mark.asyncio
async def test_rejects_null_bytes() -> None:
    with pytest.raises(ValidationAppError, match="null bytes"):
        await read_and_validate_upload(_upload(content=b"hello\x00world"))


@pytest.mark.asyncio
async def test_rejects_binary_content() -> None:
    binary = bytes([0xFF, 0xFE, 0xFD] * 1000)
    with pytest.raises(ValidationAppError, match="binary"):
        await read_and_validate_upload(_upload(content=binary))


@pytest.mark.asyncio
async def test_rejects_invalid_extension() -> None:
    with pytest.raises(ValidationAppError, match="Unsupported file type"):
        await read_and_validate_upload(_upload(filename="payload.exe"))


@pytest.mark.asyncio
async def test_rejects_too_many_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_LOG_LINES", "2")
    get_settings.cache_clear()
    content = b"a\nb\nc\n"
    with pytest.raises(ValidationAppError, match="line count"):
        await read_and_validate_upload(_upload(content=content))


@pytest.mark.asyncio
async def test_accepts_path_stripped_log_filename() -> None:
    text = await read_and_validate_upload(
        _upload(filename="../../etc/passwd.log", content=b"ok\n")
    )
    assert text == "ok\n"


@pytest.mark.asyncio
async def test_accepts_valid_utf8_log() -> None:
    text = await read_and_validate_upload(_upload(content=b"INFO started\n"))
    assert text == "INFO started\n"
