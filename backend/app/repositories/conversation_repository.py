from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message, MessageRole


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: UUID,
        title: str,
        provider: str,
        organization_id: UUID | None = None,
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            title=title[:255],
            provider=provider,
            organization_id=organization_id,
        )
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def get_for_user(
        self, conversation_id: UUID, user_id: UUID
    ) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[Conversation], int]:
        base = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        count_result = await self.session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(count_result.scalar_one())

        result = await self.session.execute(base.limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def delete_for_user(self, conversation_id: UUID, user_id: UUID) -> bool:
        conversation = await self.get_for_user(conversation_id, user_id)
        if conversation is None:
            return False
        await self.session.delete(conversation)
        await self.session.flush()
        return True

    async def add_message(
        self,
        *,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def get_recent_messages(
        self, conversation_id: UUID, limit: int
    ) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages
