from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class PageParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SortParams(BaseModel):
    sort_by: str = Field(default="created_at")
    sort_order: Literal["asc", "desc"] = "desc"


def create_sort_params(
    allowed_fields: frozenset[str],
    *,
    default_field: str = "created_at",
) -> type[SortParams]:
    """Build a SortParams model that restricts sort_by to an allowlist."""
    if default_field not in allowed_fields:
        raise ValueError("default_field must be in allowed_fields")

    class _SortParams(SortParams):
        sort_by: str = Field(default=default_field)

        @field_validator("sort_by")
        @classmethod
        def validate_sort_by(cls, value: str) -> str:
            if value not in allowed_fields:
                allowed = ", ".join(sorted(allowed_fields))
                raise ValueError(f"Invalid sort field. Allowed: {allowed}")
            return value

    _SortParams.__name__ = "SortParams"
    return _SortParams


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
