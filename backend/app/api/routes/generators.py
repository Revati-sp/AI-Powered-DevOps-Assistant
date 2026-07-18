from fastapi import APIRouter, Request

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import LLMRateLimit
from app.schemas.common import APIResponse
from app.schemas.generators import (
    DockerfileRequest,
    DockerfileResponse,
    KubernetesRequest,
    KubernetesResponse,
    PipelineRequest,
    PipelineResponse,
    ShellCommandRequest,
    ShellCommandResponse,
)
from app.services.docker_generator import DockerGeneratorService
from app.services.kubernetes_generator import KubernetesGeneratorService
from app.services.pipeline_generator import PipelineGeneratorService
from app.services.shell_command_service import ShellCommandService
from app.utils.request_context import build_audit_context

router = APIRouter(prefix="/generate", tags=["generators"])


@router.post("/dockerfile", response_model=APIResponse[DockerfileResponse])
async def generate_dockerfile(
    payload: DockerfileRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: LLMRateLimit,
) -> APIResponse[DockerfileResponse]:
    result = await DockerGeneratorService(db).generate(
        current_user, payload, audit_context=build_audit_context(request)
    )
    return APIResponse(success=True, data=result)


@router.post("/kubernetes", response_model=APIResponse[KubernetesResponse])
async def generate_kubernetes(
    payload: KubernetesRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: LLMRateLimit,
) -> APIResponse[KubernetesResponse]:
    result = await KubernetesGeneratorService(db).generate(
        current_user, payload, audit_context=build_audit_context(request)
    )
    return APIResponse(success=True, data=result)


@router.post("/pipeline", response_model=APIResponse[PipelineResponse])
async def generate_pipeline(
    payload: PipelineRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: LLMRateLimit,
) -> APIResponse[PipelineResponse]:
    result = await PipelineGeneratorService(db).generate(
        current_user, payload, audit_context=build_audit_context(request)
    )
    return APIResponse(success=True, data=result)


@router.post("/command", response_model=APIResponse[ShellCommandResponse])
async def generate_command(
    payload: ShellCommandRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: LLMRateLimit,
) -> APIResponse[ShellCommandResponse]:
    result = await ShellCommandService(db).generate(
        current_user, payload, audit_context=build_audit_context(request)
    )
    return APIResponse(success=True, data=result)
