from fastapi import APIRouter, Request

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import APIRateLimit, AuthRateLimit
from app.schemas.common import APIResponse
from app.schemas.invitation import InvitationAcceptResponse, InvitationTokenRequest
from app.services.invitation_service import InvitationService
from app.utils.request_context import build_audit_context

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("/accept", response_model=APIResponse[InvitationAcceptResponse])
async def accept_invitation(
    payload: InvitationTokenRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[InvitationAcceptResponse]:
    data = await InvitationService(db).accept(
        current_user,
        payload.token,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=data, message="Invitation accepted")


@router.post("/decline", response_model=APIResponse[None])
async def decline_invitation(
    payload: InvitationTokenRequest,
    request: Request,
    db: DBSession,
    _rl: AuthRateLimit,
) -> APIResponse[None]:
    await InvitationService(db).decline(
        payload.token,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=None, message="Invitation declined")
