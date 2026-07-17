from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import DBSession
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.common import APIResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=APIResponse[UserResponse])
async def register(
    payload: RegisterRequest, db: DBSession
) -> APIResponse[UserResponse]:
    user = await AuthService(db).register(payload)
    return APIResponse(success=True, data=user, message="Registration successful")


@router.post("/login", response_model=TokenResponse)
async def login(
    db: DBSession,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    # OAuth2 password bearer flow expects access_token at top level.
    return await AuthService(db).login(
        LoginRequest(username=form_data.username, password=form_data.password)
    )
