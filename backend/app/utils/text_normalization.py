from __future__ import annotations

import unicodedata


def normalize_identifier(value: str) -> str:
    """
    Normalize user-facing identifiers such as names and slugs.

    Uses NFKC compatibility decomposition. Do not use for passwords or
    arbitrary user content where byte-exact preservation is required.
    """
    return unicodedata.normalize("NFKC", value.strip())
