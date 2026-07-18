from __future__ import annotations

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def escape_csv_formula(value: str) -> str:
    """
    Prefix spreadsheet-sensitive values so CSV consumers do not execute formulas.
    """
    if not value:
        return value
    if value[0] in _FORMULA_PREFIXES:
        return "'" + value.replace("'", "''")
    return value
