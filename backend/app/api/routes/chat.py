from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import APIRateLimit, LLMRateLimit, StreamRateLimit
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
)
from app.schemas.common import APIResponse
from app.schemas.pagination import Page, PageParams, SortParams, create_sort_params
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
_ConversationSortParams = create_sort_params(
    frozenset({"created_at", "updated_at", "title"}), default_field="updated_at"
)


@router.post("", response_model=APIResponse[ChatResponse])
async def chat(
    payload: ChatRequest,
    db: DBSession,
    current_user: CurrentUser,
    _rl: LLMRateLimit,
) -> APIResponse[ChatResponse]:
    result = await ChatService(db).chat(current_user, payload)
    return APIResponse(success=True, data=result)


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: StreamRateLimit,
) -> StreamingResponse:
    service = ChatService(db)
    # Validate provider/ownership and persist user message before SSE starts.
    conversation, prompt, provider_name, provider = await service.prepare_stream(
        current_user, payload
    )
    generator = service.iter_stream_events(
        conversation=conversation,
        prompt=prompt,
        provider_name=provider_name,
        provider=provider,
        request=request,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations", response_model=APIResponse[Page[ConversationSummary]])
async def list_conversations(
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
    pagination: Annotated[PageParams, Depends()],
    sorting: Annotated[SortParams, Depends(_ConversationSortParams)],
    search: str | None = Query(default=None, max_length=255),
    provider: str | None = Query(default=None, max_length=50),
    organization_id: UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> APIResponse[Page[ConversationSummary]]:
    data = await ChatService(db).list_conversations(
        current_user,
        limit=pagination.limit,
        offset=pagination.offset,
        search=search,
        provider=provider,
        organization_id=organization_id,
        created_from=created_from,
        created_to=created_to,
        sort_by=sorting.sort_by,
        sort_order=sorting.sort_order,
    )
    return APIResponse(success=True, data=data)


@router.get(
    "/conversations/{conversation_id}",
    response_model=APIResponse[ConversationDetail],
)
async def get_conversation(
    conversation_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[ConversationDetail]:
    data = await ChatService(db).get_conversation(current_user, conversation_id)
    return APIResponse(success=True, data=data)


@router.delete(
    "/conversations/{conversation_id}",
    response_model=APIResponse[dict[str, str]],
)
async def delete_conversation(
    conversation_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[dict[str, str]]:
    await ChatService(db).delete_conversation(current_user, conversation_id)
    return APIResponse(success=True, data={"status": "deleted"})
