from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.config import get_settings


def _password_field() -> Any:
    settings = get_settings()
    return Field(
        min_length=settings.password_min_length,
        max_length=settings.password_max_length,
    )


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    password: str = _password_field()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = _password_field()


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = _password_field()


class VerifyEmailRequest(BaseModel):
    token: str


class SessionResponse(BaseModel):
    id: UUID
    created_at: datetime
    expires_at: datetime
    revoked: bool
    approx_ip: str | None = None
    approx_client: str | None = None
    is_current: bool = False
