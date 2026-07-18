from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import APIRateLimit
from app.schemas.common import APIResponse
from app.schemas.onboarding import UserOnboardingPatchRequest, UserOnboardingResponse
from app.schemas.user import UserResponse
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[UserResponse]:
    return APIResponse(success=True, data=UserResponse.model_validate(current_user))


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
