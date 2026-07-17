from fastapi import APIRouter

from app.api.dependencies import CurrentUser
from app.schemas.common import APIResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(current_user: CurrentUser) -> APIResponse[UserResponse]:
    return APIResponse(success=True, data=UserResponse.model_validate(current_user))
