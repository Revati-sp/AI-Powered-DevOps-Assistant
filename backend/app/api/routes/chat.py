from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DBSession
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
)
from app.schemas.common import APIResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=APIResponse[ChatResponse])
async def chat(
    payload: ChatRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ChatResponse]:
    result = await ChatService(db).chat(current_user, payload)
    return APIResponse(success=True, data=result)


@router.get("/conversations", response_model=APIResponse[list[ConversationSummary]])
async def list_conversations(
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[list[ConversationSummary]]:
    data = await ChatService(db).list_conversations(current_user)
    return APIResponse(success=True, data=data)


@router.get(
    "/conversations/{conversation_id}",
    response_model=APIResponse[ConversationDetail],
)
async def get_conversation(
    conversation_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
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
) -> APIResponse[dict[str, str]]:
    await ChatService(db).delete_conversation(current_user, conversation_id)
    return APIResponse(success=True, data={"status": "deleted"})
