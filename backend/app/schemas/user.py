from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole
from app.schemas.common import ORMModel


class UserProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_\-\.]+$",
    )
    display_name: str | None = Field(default=None, max_length=120)
    timezone: str | None = Field(default=None, max_length=64)
    job_title: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=512)


class EmailChangeRequest(BaseModel):
    new_email: EmailStr
    password: str


class EmailChangeConfirmRequest(BaseModel):
    token: str


class EmailChangeMessageResponse(BaseModel):
    message: str


class UserResponse(ORMModel):
    id: UUID
    email: str
    username: str
    role: UserRole
    is_active: bool
    email_verified_at: datetime | None = None
    display_name: str | None = None
    timezone: str | None = None
    job_title: str | None = None
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime
