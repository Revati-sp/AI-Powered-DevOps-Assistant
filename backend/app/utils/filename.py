from __future__ import annotations

import re
from pathlib import PurePath

_UNSAFE_FILENAME_CHARS = re.compile(r'[\x00-\x1f\x7f<>:"/\\|?*]')
_WHITESPACE = re.compile(r"\s+")


def sanitize_filename(filename: str, *, max_length: int = 255) -> str:
    """
    Reduce an upload filename to a safe basename.

    Strips directory components, replaces unsafe characters, and truncates
    while preserving the extension when possible.
    """
    basename = PurePath(filename or "upload").name
    basename = _UNSAFE_FILENAME_CHARS.sub("_", basename)
    basename = _WHITESPACE.sub("_", basename).strip("._")
    if not basename or basename in {".", ".."}:
        basename = "upload"

    if len(basename) <= max_length:
        return basename

    suffix = PurePath(basename).suffix
    stem = PurePath(basename).stem
    max_stem_len = max(1, max_length - len(suffix))
    return f"{stem[:max_stem_len]}{suffix}"
