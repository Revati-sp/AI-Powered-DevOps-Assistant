from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.organization import OrgRole
from app.schemas.common import ORMModel


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=100)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=100)


class AddMemberRequest(BaseModel):
    email: EmailStr
    role: OrgRole = OrgRole.MEMBER


class UpdateMemberRequest(BaseModel):
    role: OrgRole


class OrganizationResponse(ORMModel):
    id: UUID
    name: str
    slug: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class OrganizationMemberResponse(ORMModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    role: OrgRole
    email: str
    username: str
    created_at: datetime
    updated_at: datetime
