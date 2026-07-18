from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")

DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSession,
) -> User:
    payload = decode_access_token(token)
    try:
        user_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError(
            "Invalid token subject", code=ErrorCode.UNAUTHORIZED
        ) from exc

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError(
            "User not found or inactive", code=ErrorCode.UNAUTHORIZED
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin privileges required")
    return user


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session
