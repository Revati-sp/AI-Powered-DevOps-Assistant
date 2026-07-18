from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import APIRateLimit, AuthRateLimit
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionResponse,
    TokenPairResponse,
    VerifyEmailRequest,
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


@router.post("/forgot-password", response_model=APIResponse[dict[str, str]])
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: DBSession,
    _rl: AuthRateLimit,
) -> APIResponse[dict[str, str]]:
    message = await AuthService(db).forgot_password(
        payload.email,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data={"message": message}, message=message)


@router.post("/reset-password", response_model=APIResponse[None])
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: DBSession,
    _rl: AuthRateLimit,
) -> APIResponse[None]:
    await AuthService(db).reset_password(
        payload,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=None, message="Password reset successful")


@router.post("/change-password", response_model=APIResponse[None])
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    db: DBSession,
    current_user: CurrentUser,
    _rl: AuthRateLimit,
    x_refresh_token: str | None = Header(default=None, alias="X-Refresh-Token"),
) -> APIResponse[None]:
    await AuthService(db).change_password(
        current_user,
        payload,
        current_refresh_token=x_refresh_token,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=None, message="Password changed successfully")


@router.post("/send-verification", response_model=APIResponse[None])
async def send_verification(
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[None]:
    await AuthService(db).send_verification_email(
        current_user,
        audit_context=build_audit_context(request),
    )
    return APIResponse(
        success=True,
        data=None,
        message="Verification email sent",
    )


@router.post("/verify-email", response_model=APIResponse[UserResponse])
async def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    db: DBSession,
    _rl: AuthRateLimit,
) -> APIResponse[UserResponse]:
    user = await AuthService(db).verify_email(
        payload.token,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=user, message="Email verified successfully")


@router.get("/sessions", response_model=APIResponse[list[SessionResponse]])
async def list_sessions(
    db: DBSession,
    current_user: CurrentUser,
    _rl: AuthRateLimit,
    x_refresh_token: str | None = Header(default=None, alias="X-Refresh-Token"),
    refresh_token: str | None = Query(default=None),
) -> APIResponse[list[SessionResponse]]:
    current_token = x_refresh_token or refresh_token
    sessions = await AuthService(db).list_sessions(
        current_user,
        current_refresh_token=current_token,
    )
    return APIResponse(success=True, data=sessions)


@router.delete("/sessions/{session_id}", response_model=APIResponse[None])
async def revoke_session(
    session_id: UUID,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: AuthRateLimit,
) -> APIResponse[None]:
    await AuthService(db).revoke_session(
        current_user,
        session_id,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=None, message="Session revoked")
