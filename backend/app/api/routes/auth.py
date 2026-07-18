from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import AuthRateLimit
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
)
from app.schemas.common import APIResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.utils.request_context import build_audit_context

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=APIResponse[UserResponse])
async def register(
    payload: RegisterRequest,
    db: DBSession,
    _rl: AuthRateLimit,
) -> APIResponse[UserResponse]:
    user = await AuthService(db).register(payload)
    return APIResponse(success=True, data=user, message="Registration successful")


@router.post("/login", response_model=TokenPairResponse)
async def login(
    request: Request,
    db: DBSession,
    _rl: AuthRateLimit,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> TokenPairResponse:
    # OAuth2 password bearer flow expects access_token at top level.
    return await AuthService(db).login(
        LoginRequest(username=form_data.username, password=form_data.password),
        audit_context=build_audit_context(request),
    )


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh_tokens(
    request: Request,
    payload: RefreshRequest,
    db: DBSession,
    _rl: AuthRateLimit,
) -> TokenPairResponse:
    return await AuthService(db).refresh(
        payload.refresh_token,
        audit_context=build_audit_context(request),
    )


@router.post("/logout", response_model=APIResponse[None])
async def logout(
    request: Request,
    payload: LogoutRequest,
    db: DBSession,
    _rl: AuthRateLimit,
) -> APIResponse[None]:
    await AuthService(db).logout(
        payload.refresh_token,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=None, message="Logged out successfully")


@router.post("/logout-all", response_model=APIResponse[None])
async def logout_all(
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: AuthRateLimit,
) -> APIResponse[None]:
    await AuthService(db).logout_all(
        current_user,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=None, message="All sessions revoked")
