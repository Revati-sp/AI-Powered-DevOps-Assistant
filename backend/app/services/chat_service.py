from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.models.message import MessageRole
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
)
from app.services.llm.factory import get_llm_provider
from app.services.llm.prompts import DEVOPS_SYSTEM_PROMPT
from app.utils.sanitization import sanitize_text


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.conversations = ConversationRepository(session)
        self.settings = get_settings()

    async def chat(self, user: User, payload: ChatRequest) -> ChatResponse:
        message = sanitize_text(payload.message, max_length=8000)
        provider = get_llm_provider(payload.provider)

        if payload.conversation_id:
            conversation = await self.conversations.get_for_user(
                payload.conversation_id, user.id
            )
            if conversation is None:
                raise NotFoundError("Conversation not found")
        else:
            title = message[:80] or "New conversation"
            conversation = await self.conversations.create(
                user_id=user.id,
                title=title,
                provider=provider.name,
            )

        history = await self.conversations.get_recent_messages(
            conversation.id, self.settings.chat_history_limit
        )
        history_block = "\n".join(
            f"{msg.role.value.upper()}: {msg.content}" for msg in history
        )
        prompt = (
            "Conversation history (most recent first limited):\n"
            f"{history_block or '(none)'}\n\n"
            f"USER: {message}\n\n"
            "Respond as the DevOps assistant. Do not claim any command was executed."
        )

        answer = await provider.generate(prompt, system_prompt=DEVOPS_SYSTEM_PROMPT)
        await self.conversations.add_message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=message,
        )
        assistant_message = await self.conversations.add_message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=answer,
        )
        conversation.provider = provider.name
        await self.session.flush()

        return ChatResponse(
            conversation_id=conversation.id,
            answer=answer,
            provider=provider.name,
            created_at=assistant_message.created_at,
        )

    async def list_conversations(self, user: User) -> list[ConversationSummary]:
        rows = await self.conversations.list_for_user(user.id)
        return [ConversationSummary.model_validate(row) for row in rows]

    async def get_conversation(
        self, user: User, conversation_id: UUID
    ) -> ConversationDetail:
        conversation = await self.conversations.get_for_user(conversation_id, user.id)
        if conversation is None:
            raise NotFoundError("Conversation not found")
        return ConversationDetail.model_validate(conversation)

    async def delete_conversation(self, user: User, conversation_id: UUID) -> None:
        deleted = await self.conversations.delete_for_user(conversation_id, user.id)
        if not deleted:
            raise NotFoundError("Conversation not found")
