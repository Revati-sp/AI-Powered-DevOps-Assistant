from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.organization import OrgRole
from app.models.organization_invitation import InvitationStatus
from app.schemas.common import ORMModel


class CreateInvitationRequest(BaseModel):
    email: EmailStr
    role: OrgRole = OrgRole.MEMBER


class InvitationTokenRequest(BaseModel):
    token: str


class InvitationResponse(ORMModel):
    id: UUID
    organization_id: UUID
    email: str
    role: OrgRole
    status: InvitationStatus
    invited_by_user_id: UUID
    expires_at: datetime
    accepted_at: datetime | None = None
    declined_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime


class InvitationAcceptResponse(BaseModel):
    organization_id: UUID
    organization_name: str
    role: OrgRole
    message: str = Field(default="Invitation accepted")
