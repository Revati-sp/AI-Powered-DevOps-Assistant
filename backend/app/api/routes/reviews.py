from fastapi import APIRouter, Request

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import LLMRateLimit
from app.schemas.common import APIResponse
from app.schemas.reviews import ReviewRequest, ReviewResponse
from app.services.security_review_service import SecurityReviewService
from app.utils.request_context import build_audit_context

router = APIRouter(tags=["reviews"])


@router.post("/review", response_model=APIResponse[ReviewResponse])
async def review_configuration(
    payload: ReviewRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: LLMRateLimit,
) -> APIResponse[ReviewResponse]:
    result = await SecurityReviewService(db).review(
        current_user, payload, audit_context=build_audit_context(request)
    )
    return APIResponse(success=True, data=result)
