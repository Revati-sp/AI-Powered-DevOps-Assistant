from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)

    async def register(self, payload: RegisterRequest) -> UserResponse:
        if await self.users.get_by_email(payload.email):
            raise ConflictError("Email already registered")
        if await self.users.get_by_username(payload.username):
            raise ConflictError("Username already taken")

        user = await self.users.create(
            email=payload.email,
            username=payload.username,
            hashed_password=hash_password(payload.password),
        )
        return UserResponse.model_validate(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.users.get_by_username(payload.username)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Incorrect username or password")
        if not user.is_active:
            raise UnauthorizedError("User account is inactive")

        token = create_access_token(
            user.id,
            extra_claims={"role": user.role.value, "username": user.username},
        )
        return TokenResponse(access_token=token)

    async def get_current_user_response(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)
