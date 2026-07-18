import pytest
from app.models.user import User, UserRole
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService

from tests.conftest import FakeLLMProvider


@pytest.mark.asyncio
async def test_chat_service_with_mocked_llm(
    db_session, fake_llm: FakeLLMProvider
) -> None:
    user = User(
        email="chat@example.com",
        username="chatuser",
        hashed_password="hashed",
        role=UserRole.USER,
    )
    db_session.add(user)
    await db_session.flush()

    import app.services.provider_service as provider_module

    provider_module.get_llm_provider = lambda provider_name=None: fake_llm  # type: ignore[assignment]

    service = ChatService(db_session)
    result = await service.chat(
        user,
        ChatRequest(message="How do I debug CrashLoopBackOff?", provider="gemini"),
    )
    assert result.provider == "gemini"
    assert result.answer
    assert fake_llm.calls
