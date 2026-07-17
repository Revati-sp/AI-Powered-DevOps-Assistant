from fastapi import APIRouter, File, Form, UploadFile

from app.api.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.common import APIResponse
from app.schemas.logs import (
    AsyncTaskResponse,
    LogAnalyzeRequest,
    LogAnalyzeResult,
    TaskStatusResponse,
)
from app.services.log_analyzer import LogAnalyzerService
from app.utils.file_validation import read_and_validate_upload

router = APIRouter(tags=["logs"])


@router.post("/logs/analyze", response_model=APIResponse[LogAnalyzeResult])
async def analyze_logs(
    payload: LogAnalyzeRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[LogAnalyzeResult]:
    result = await LogAnalyzerService(db).analyze(
        current_user, payload.content, provider_name=payload.provider
    )
    return APIResponse(success=True, data=result)


@router.post("/logs/analyze/upload", response_model=APIResponse[LogAnalyzeResult])
async def analyze_logs_upload(
    db: DBSession,
    current_user: CurrentUser,
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
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[AsyncTaskResponse]:
    result = await LogAnalyzerService(db).enqueue_async(
        current_user, payload.content, provider_name=payload.provider
    )
    return APIResponse(success=True, data=result)


@router.get("/tasks/{task_id}", response_model=APIResponse[TaskStatusResponse])
async def get_task_status(
    task_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[TaskStatusResponse]:
    analysis = await ArtifactRepository(db).get_analysis_by_task_id(task_id)
    if analysis is None or analysis.user_id != current_user.id:
        raise NotFoundError("Task not found")

    error = None
    if analysis.result_json and analysis.status.value == "failed":
        error = str(analysis.result_json.get("error"))

    return APIResponse(
        success=True,
        data=TaskStatusResponse(
            task_id=task_id,
            status=analysis.status.value,
            result=analysis.result_json,
            error=error,
        ),
    )
