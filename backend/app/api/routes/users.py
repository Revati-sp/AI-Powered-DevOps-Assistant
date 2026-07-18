from fastapi import APIRouter, Request

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import APIRateLimit, AuthRateLimit
from app.schemas.common import APIResponse
from app.schemas.onboarding import UserOnboardingPatchRequest, UserOnboardingResponse
from app.schemas.user import (
    EmailChangeConfirmRequest,
    EmailChangeMessageResponse,
    EmailChangeRequest,
    UserProfileUpdateRequest,
    UserResponse,
)
from app.services.onboarding_service import OnboardingService
from app.services.profile_service import ProfileService
from app.utils.request_context import build_audit_context

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[UserResponse]:
    return APIResponse(success=True, data=UserResponse.model_validate(current_user))


@router.patch("/me", response_model=APIResponse[UserResponse])
async def update_me(
    request: Request,
    payload: UserProfileUpdateRequest,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[UserResponse]:
    user = await ProfileService(db).update_profile(
        current_user,
        payload,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=user)


@router.post(
    "/me/email-change/request",
    response_model=APIResponse[EmailChangeMessageResponse],
)
async def request_my_email_change(
    request: Request,
    payload: EmailChangeRequest,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[EmailChangeMessageResponse]:
    message = await ProfileService(db).request_email_change(
        current_user,
        str(payload.new_email),
        payload.password,
        audit_context=build_audit_context(request),
        request_ip=request.client.host if request.client else None,
    )
    return APIResponse(
        success=True,
        data=EmailChangeMessageResponse(message=message),
        message=message,
    )


@router.post(
    "/me/email-change/confirm",
    response_model=APIResponse[UserResponse],
)
async def confirm_my_email_change(
    request: Request,
    payload: EmailChangeConfirmRequest,
    db: DBSession,
    _rl: AuthRateLimit,
) -> APIResponse[UserResponse]:
    user = await ProfileService(db).confirm_email_change(
        payload.token,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=user, message="Email changed successfully")


@router.get("/me/onboarding", response_model=APIResponse[UserOnboardingResponse])
async def get_my_onboarding(
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[UserOnboardingResponse]:
    onboarding = await OnboardingService(db).get_onboarding(current_user)
    return APIResponse(
        success=True,
        data=UserOnboardingResponse.model_validate(onboarding),
    )


@router.patch("/me/onboarding", response_model=APIResponse[UserOnboardingResponse])
async def patch_my_onboarding(
    payload: UserOnboardingPatchRequest,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[UserOnboardingResponse]:
    onboarding = await OnboardingService(db).patch_onboarding(
        current_user,
        welcome_dismissed=payload.welcome_dismissed,
        profile_completed=payload.profile_completed,
        first_chat_completed=payload.first_chat_completed,
        first_artifact_created=payload.first_artifact_created,
        organization_created=payload.organization_created,
        invite_team_completed=payload.invite_team_completed,
        tour_completed=payload.tour_completed,
        onboarding_completed=payload.onboarding_completed,
    )
    return APIResponse(
        success=True,
        data=UserOnboardingResponse.model_validate(onboarding),
    )
