from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DBSession
from app.schemas.common import APIResponse
from app.schemas.reviews import ReviewRequest, ReviewResponse
from app.services.security_review_service import SecurityReviewService

router = APIRouter(tags=["reviews"])


@router.post("/review", response_model=APIResponse[ReviewResponse])
async def review_configuration(
    payload: ReviewRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ReviewResponse]:
    result = await SecurityReviewService(db).review(current_user, payload)
    return APIResponse(success=True, data=result)
