from fastapi import APIRouter, File, Form, Header, Request, UploadFile

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import UploadRateLimit
from app.schemas.common import APIResponse
from app.schemas.logs import AsyncTaskResponse, LogAnalyzeRequest, LogAnalyzeResult
from app.services.log_analyzer import LogAnalyzerService
from app.utils.file_validation import read_and_validate_upload
from app.utils.request_context import build_audit_context

router = APIRouter(tags=["logs"])


@router.post("/logs/analyze", response_model=APIResponse[LogAnalyzeResult])
async def analyze_logs(
    payload: LogAnalyzeRequest,
    db: DBSession,
    current_user: CurrentUser,
    _rl: UploadRateLimit,
) -> APIResponse[LogAnalyzeResult]:
    result = await LogAnalyzerService(db).analyze(
        current_user, payload.content, provider_name=payload.provider
    )
    return APIResponse(success=True, data=result)


@router.post("/logs/analyze/upload", response_model=APIResponse[LogAnalyzeResult])
async def analyze_logs_upload(
    db: DBSession,
    current_user: CurrentUser,
    _rl: UploadRateLimit,
    file: UploadFile = File(...),
    provider: str = Form(default="gemini"),
) -> APIResponse[LogAnalyzeResult]:
    content = await read_and_validate_upload(file)
    result = await LogAnalyzerService(db).analyze(
        current_user, content, provider_name=provider
    )
    return APIResponse(success=True, data=result)


@router.post("/logs/analyze/async", response_model=APIResponse[AsyncTaskResponse])
async def analyze_logs_async(
    payload: LogAnalyzeRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: UploadRateLimit,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> APIResponse[AsyncTaskResponse]:
    result = await LogAnalyzerService(db).enqueue_async(
        current_user,
        payload.content,
        provider_name=payload.provider,
        idempotency_key=idempotency_key,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=result)
