from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError, NotFoundError
from app.core.logging import get_logger
from app.models.conversation import Conversation
from app.models.message import MessageRole
from app.models.provider_config import LLMOperation
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
)
from app.schemas.pagination import Page
from app.services.llm.base import LLMProvider
from app.services.llm.gateway import LLMGateway
from app.services.llm.prompts import DEVOPS_SYSTEM_PROMPT
from app.services.onboarding_service import OnboardingService
from app.services.rbac import OrganizationAuthService, Permission
from app.services.usage_quota_service import UsageQuotaService
from app.utils.sanitization import sanitize_text
from app.utils.sse import encode_sse

logger = get_logger(__name__)


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.conversations = ConversationRepository(session)
        self.org_auth = OrganizationAuthService(session)
        self.settings = get_settings()

    async def _resolve_organization_id(
        self, user: User, organization_id: UUID | None
    ) -> UUID | None:
        if organization_id is None:
            return None
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.RESOURCE_CREATE
        )
        return organization_id

    async def _mark_first_chat(self, user_id: UUID) -> None:
        try:
            await OnboardingService(self.session).mark_flag(
                user_id, first_chat_completed=True
            )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to mark first_chat_completed onboarding flag")

    def _build_prompt(self, history_block: str, message: str) -> str:
        return (
            "Conversation history (most recent first limited):\n"
            f"{history_block or '(none)'}\n\n"
            f"USER: {message}\n\n"
            "Respond as the DevOps assistant. Do not claim any command was executed."
        )

    async def chat(self, user: User, payload: ChatRequest) -> ChatResponse:
        message = sanitize_text(payload.message, max_length=8000)
        organization_id = await self._resolve_organization_id(
            user, payload.organization_id
        )
        initial_provider = (payload.provider or self.settings.llm_provider).lower()

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
                provider=initial_provider,
                organization_id=organization_id,
            )

        history = await self.conversations.get_recent_messages(
            conversation.id, self.settings.chat_history_limit
        )
        history_block = "\n".join(
            f"{msg.role.value.upper()}: {msg.content}" for msg in history
        )
        prompt = self._build_prompt(history_block, message)

        gateway = LLMGateway(self.session)
        answer, provider_name = await gateway.generate(
            user=user,
            operation=LLMOperation.CHAT,
            organization_id=organization_id,
            prompt=prompt,
            system_prompt=DEVOPS_SYSTEM_PROMPT,
            explicit_provider=payload.provider,
        )
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
        conversation.provider = provider_name
        await self._mark_first_chat(user.id)
        await self.session.flush()

        return ChatResponse(
            conversation_id=conversation.id,
            answer=answer,
            provider=provider_name,
            created_at=assistant_message.created_at,
        )

    async def prepare_stream(
        self, user: User, payload: ChatRequest
    ) -> tuple[Conversation, str, str, LLMProvider]:
        """Validate ownership, persist user message, return stream context.

        Raises HTTP-safe application errors before SSE begins.
        """
        message = sanitize_text(payload.message, max_length=8000)
        organization_id = await self._resolve_organization_id(
            user, payload.organization_id
        )
        gateway = LLMGateway(self.session)
        provider, provider_name = await gateway.resolve_stream_provider(
            user=user,
            operation=LLMOperation.CHAT,
            organization_id=organization_id,
            estimated_tokens=max(1, len(message) // 4),
            explicit_provider=payload.provider,
        )

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
                provider=provider_name,
                organization_id=organization_id,
            )

        await self.conversations.add_message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=message,
        )
        conversation.provider = provider_name
        await self.session.flush()
        await self.session.commit()

        history = await self.conversations.get_recent_messages(
            conversation.id, self.settings.chat_history_limit
        )
        prior = history[:-1] if history and history[-1].content == message else history
        history_block = "\n".join(
            f"{msg.role.value.upper()}: {msg.content}" for msg in prior
        )
        prompt = self._build_prompt(history_block, message)
        return conversation, prompt, provider_name, provider

    async def iter_stream_events(
        self,
        *,
        conversation: Conversation,
        prompt: str,
        provider_name: str,
        provider: LLMProvider,
        request: Request,
    ) -> AsyncIterator[str]:
        yield encode_sse("conversation", {"conversation_id": str(conversation.id)})

        heartbeat_interval = self.settings.sse_heartbeat_interval_seconds
        queue: asyncio.Queue[tuple[str, dict[str, Any] | None]] = asyncio.Queue()
        stop = asyncio.Event()

        async def produce_tokens() -> None:
            accumulated = ""
            try:
                async for chunk in provider.stream(
                    prompt, system_prompt=DEVOPS_SYSTEM_PROMPT
                ):
                    if stop.is_set() or await request.is_disconnected():
                        break
                    accumulated += chunk
                    await queue.put(("token", {"content": chunk}))

                if stop.is_set() or await request.is_disconnected():
                    await queue.put(("cancelled", None))
                    return

                assistant_message = await self.conversations.add_message(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=accumulated,
                )
                await UsageQuotaService(self.session).record_llm_usage(
                    user_id=conversation.user_id,
                    organization_id=conversation.organization_id,
                    operation=LLMOperation.CHAT.value,
                    provider=provider_name,
                    model=None,
                    input_tokens=max(1, len(prompt) // 4),
                    output_tokens=max(1, len(accumulated) // 4),
                    is_estimated=True,
                )
                await self._mark_first_chat(conversation.user_id)
                await self.session.commit()
                await queue.put(
                    (
                        "completed",
                        {
                            "message_id": str(assistant_message.id),
                            "provider": provider_name,
                        },
                    )
                )
            except asyncio.CancelledError:
                await queue.put(("cancelled", None))
                raise
            except LLMProviderError:
                logger.warning(
                    "Streaming LLM provider failed",
                    extra={"provider": provider_name},
                )
                await queue.put(
                    (
                        "error",
                        {
                            "code": "LLM_STREAM_ERROR",
                            "message": "The AI response could not be completed.",
                        },
                    )
                )
            except Exception:  # noqa: BLE001
                logger.exception("Unexpected streaming failure")
                await queue.put(
                    (
                        "error",
                        {
                            "code": "LLM_STREAM_ERROR",
                            "message": "The AI response could not be completed.",
                        },
                    )
                )
            finally:
                await queue.put(("done", None))

        producer = asyncio.create_task(produce_tokens())
        try:
            while True:
                if await request.is_disconnected():
                    stop.set()
                    producer.cancel()
                    break
                try:
                    event, data = await asyncio.wait_for(
                        queue.get(), timeout=heartbeat_interval
                    )
                except TimeoutError:
                    yield encode_sse("heartbeat", {"status": "active"})
                    continue

                if event in {"done", "cancelled"}:
                    break
                if event == "token" and data is not None:
                    yield encode_sse("token", data)
                elif event == "completed" and data is not None:
                    yield encode_sse("completed", data)
                    break
                elif event == "error" and data is not None:
                    yield encode_sse("error", data)
                    break
        finally:
            stop.set()
            if not producer.done():
                producer.cancel()
                try:
                    await producer
                except asyncio.CancelledError:
                    pass

    async def list_conversations(
        self,
        user: User,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
        provider: str | None = None,
        organization_id: UUID | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Page[ConversationSummary]:
        if organization_id is not None:
            await self.org_auth.require_membership(organization_id, user.id)
        rows, total = await self.conversations.list_for_user(
            user.id,
            limit=limit,
            offset=offset,
            search=search,
            provider=provider,
            organization_id=organization_id,
            created_from=created_from,
            created_to=created_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return Page(
            items=[ConversationSummary.model_validate(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

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
