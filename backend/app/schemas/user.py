from datetime import datetime
from uuid import UUID

from app.models.user import UserRole
from app.schemas.common import ORMModel


class UserResponse(ORMModel):
    id: UUID
    email: str
    username: str
    role: UserRole
    is_active: bool
    email_verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
