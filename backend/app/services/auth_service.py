from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_secure_token,
    hash_password,
    hash_refresh_token,
    hash_secure_token,
    needs_rehash,
    validate_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.email_verification_token_repository import (
    EmailVerificationTokenRepository,
)
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionResponse,
    TokenPairResponse,
)
from app.schemas.user import UserResponse
from app.services.audit_service import AuditRequestContext, AuditService
from app.services.email_service import EmailService
from app.utils.session_helpers import refresh_token_to_session

GENERIC_AUTH_ERROR = "Invalid authentication credentials."
GENERIC_RESET_SENT_MESSAGE = (
    "If an account exists for that email, a reset link has been sent."
)
INVALID_TOKEN_ERROR = "Invalid or expired token."


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)
        self.password_reset_tokens = PasswordResetTokenRepository(session)
        self.email_verification_tokens = EmailVerificationTokenRepository(session)
        self.audit = AuditService(session)
        self.email = EmailService()

    async def register(self, payload: RegisterRequest) -> UserResponse:
        validate_password(
            payload.password,
            username=payload.username,
            email=payload.email,
        )
        if await self.users.get_by_email(payload.email):
            raise ConflictError("Email already registered")
        if await self.users.get_by_username(payload.username):
            raise ConflictError("Username already taken")

        user = await self.users.create(
            email=payload.email,
            username=payload.username,
            hashed_password=hash_password(payload.password),
        )
        settings = get_settings()
        if settings.email_verification_required:
            await self.send_verification_email(user, audit_context=None)
        return UserResponse.model_validate(user)

    async def login(
        self,
        payload: LoginRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> TokenPairResponse:
        user = await self.users.get_by_username(payload.username)
        if user is None or not verify_password(payload.password, user.hashed_password):
            await self.audit.record_event(
                action="user.login.failure",
                actor_user_id=user.id if user else None,
                organization_id=None,
                resource_type="user",
                resource_id=user.id if user else None,
                request_context=audit_context,
                metadata={"username": payload.username},
            )
            raise UnauthorizedError(GENERIC_AUTH_ERROR)
        if not user.is_active:
            await self.audit.record_event(
                action="user.login.failure",
                actor_user_id=user.id,
                organization_id=None,
                resource_type="user",
                resource_id=user.id,
                request_context=audit_context,
                metadata={"reason": "inactive_account"},
            )
            raise UnauthorizedError(GENERIC_AUTH_ERROR)

        settings = get_settings()
        if settings.email_verification_required and user.email_verified_at is None:
            await self.audit.record_event(
                action="user.login.failure",
                actor_user_id=user.id,
                organization_id=None,
                resource_type="user",
                resource_id=user.id,
                request_context=audit_context,
                metadata={"reason": "email_not_verified"},
            )
            raise UnauthorizedError(GENERIC_AUTH_ERROR)

        if needs_rehash(user.hashed_password):
            await self.users.update_hashed_password(
                user.id,
                hash_password(payload.password),
            )
            await self.audit.record_event(
                action="user.password.rehashed",
                actor_user_id=user.id,
                organization_id=None,
                resource_type="user",
                resource_id=user.id,
                request_context=audit_context,
            )

        return await self._issue_token_pair(user, audit_context=audit_context)

    async def refresh(
        self,
        raw_token: str,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> TokenPairResponse:
        try:
            payload = decode_token(raw_token, expected_type="refresh")
        except UnauthorizedError:
            await self._record_refresh_failure(audit_context)
            raise UnauthorizedError(GENERIC_AUTH_ERROR) from None

        jti = str(payload["jti"])
        token_record = await self.refresh_tokens.get_by_jti_for_update(jti)
        if token_record is None:
            await self._record_refresh_failure(audit_context)
            raise UnauthorizedError(GENERIC_AUTH_ERROR)

        if token_record.used_at is not None or token_record.revoked_at is not None:
            await self.refresh_tokens.revoke_family(
                token_record.family_id,
                reason="reuse_detected",
            )
            await self.audit.record_event(
                action="user.token.reuse_detected",
                actor_user_id=token_record.user_id,
                organization_id=None,
                resource_type="refresh_token",
                resource_id=token_record.id,
                request_context=audit_context,
                metadata={"family_id": str(token_record.family_id)},
            )
            raise UnauthorizedError(GENERIC_AUTH_ERROR)

        now = datetime.now(UTC)
        if _as_utc(token_record.expires_at) <= now:
            await self._record_refresh_failure(
                audit_context, user_id=token_record.user_id
            )
            raise UnauthorizedError(GENERIC_AUTH_ERROR)

        if token_record.token_hash != hash_refresh_token(raw_token):
            await self._record_refresh_failure(
                audit_context, user_id=token_record.user_id
            )
            raise UnauthorizedError(GENERIC_AUTH_ERROR)

        try:
            user_id = UUID(str(payload["sub"]))
        except ValueError:
            await self._record_refresh_failure(
                audit_context, user_id=token_record.user_id
            )
            raise UnauthorizedError(GENERIC_AUTH_ERROR) from None

        if user_id != token_record.user_id:
            await self._record_refresh_failure(
                audit_context, user_id=token_record.user_id
            )
            raise UnauthorizedError(GENERIC_AUTH_ERROR)

        user = await self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            await self._record_refresh_failure(
                audit_context, user_id=token_record.user_id
            )
            raise UnauthorizedError(GENERIC_AUTH_ERROR)

        token_record.used_at = now
        refresh_token, new_record = await self._create_refresh_token_record(
            user,
            family_id=token_record.family_id,
            audit_context=audit_context,
        )
        token_record.replaced_by_token_id = new_record.id

        token_pair = self._build_token_pair(user, refresh_token)
        await self.audit.record_event(
            action="user.token.refreshed",
            actor_user_id=user.id,
            organization_id=None,
            resource_type="refresh_token",
            resource_id=new_record.id,
            request_context=audit_context,
            metadata={"family_id": str(token_record.family_id)},
        )
        return token_pair

    async def logout(
        self,
        raw_token: str,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        try:
            payload = decode_token(raw_token, expected_type="refresh")
        except UnauthorizedError:
            return

        token_record = await self.refresh_tokens.get_by_jti(str(payload["jti"]))
        if token_record is None:
            return
        if token_record.token_hash != hash_refresh_token(raw_token):
            return

        await self.refresh_tokens.revoke_token(token_record.id, reason="logout")
        await self.audit.record_event(
            action="user.logout",
            actor_user_id=token_record.user_id,
            organization_id=None,
            resource_type="refresh_token",
            resource_id=token_record.id,
            request_context=audit_context,
        )

    async def logout_all(
        self,
        user: User,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        revoked_count = await self.refresh_tokens.revoke_all_for_user(
            user.id,
            reason="logout_all",
        )
        await self.audit.record_event(
            action="user.logout_all",
            actor_user_id=user.id,
            organization_id=None,
            resource_type="user",
            resource_id=user.id,
            request_context=audit_context,
            metadata={"revoked_count": revoked_count},
        )

    async def get_current_user_response(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    async def forgot_password(
        self,
        email: str,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> str:
        user = await self.users.get_by_email(email.lower())
        if user is None or not user.is_active:
            return GENERIC_RESET_SENT_MESSAGE

        settings = get_settings()
        await self.password_reset_tokens.invalidate_unused_for_user(user.id)
        raw_token = generate_secure_token()
        await self.password_reset_tokens.create(
            user_id=user.id,
            token_hash=hash_secure_token(raw_token),
            expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.password_reset_token_minutes),
            created_ip=audit_context.ip_address if audit_context else None,
        )
        reset_url = f"{settings.public_frontend_url}/reset-password?token={raw_token}"
        await self.email.send_password_reset(to=user.email, reset_url=reset_url)
        await self.audit.record_event(
            action="user.password_reset.requested",
            actor_user_id=user.id,
            organization_id=None,
            resource_type="user",
            resource_id=user.id,
            request_context=audit_context,
        )
        return GENERIC_RESET_SENT_MESSAGE

    async def reset_password(
        self,
        payload: ResetPasswordRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        validate_password(payload.new_password)
        token_hash = hash_secure_token(payload.token)
        token_record = await self.password_reset_tokens.get_by_hash_for_update(
            token_hash
        )
        if token_record is None:
            raise UnauthorizedError(INVALID_TOKEN_ERROR)

        now = datetime.now(UTC)
        if token_record.used_at is not None or _as_utc(token_record.expires_at) <= now:
            raise UnauthorizedError(INVALID_TOKEN_ERROR)

        user = await self.users.get_by_id(token_record.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError(INVALID_TOKEN_ERROR)

        token_record.used_at = now
        await self.users.update_hashed_password(
            user.id,
            hash_password(payload.new_password),
        )
        await self.refresh_tokens.revoke_all_for_user(
            user.id,
            reason="password_reset",
        )
        await self.audit.record_event(
            action="user.password_reset.completed",
            actor_user_id=user.id,
            organization_id=None,
            resource_type="user",
            resource_id=user.id,
            request_context=audit_context,
        )

    async def change_password(
        self,
        user: User,
        payload: ChangePasswordRequest,
        *,
        current_refresh_token: str | None = None,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        if not verify_password(payload.current_password, user.hashed_password):
            raise UnauthorizedError(GENERIC_AUTH_ERROR)

        validate_password(
            payload.new_password,
            username=user.username,
            email=user.email,
        )
        await self.users.update_hashed_password(
            user.id,
            hash_password(payload.new_password),
        )

        keep_jti: str | None = None
        if current_refresh_token:
            try:
                token_payload = decode_token(
                    current_refresh_token, expected_type="refresh"
                )
                token_record = await self.refresh_tokens.get_by_jti(
                    str(token_payload["jti"])
                )
                if (
                    token_record is not None
                    and token_record.user_id == user.id
                    and token_record.token_hash
                    == hash_refresh_token(current_refresh_token)
                    and token_record.revoked_at is None
                ):
                    keep_jti = token_record.jti
            except UnauthorizedError:
                keep_jti = None

        if keep_jti:
            await self.refresh_tokens.revoke_all_except_jti(
                user.id,
                keep_jti=keep_jti,
                reason="password_change",
            )
        else:
            await self.refresh_tokens.revoke_all_for_user(
                user.id,
                reason="password_change",
            )

        await self.audit.record_event(
            action="user.password.changed",
            actor_user_id=user.id,
            organization_id=None,
            resource_type="user",
            resource_id=user.id,
            request_context=audit_context,
        )

    async def send_verification_email(
        self,
        user: User,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        if user.email_verified_at is not None:
            raise ConflictError("Email is already verified")

        settings = get_settings()
        await self.email_verification_tokens.invalidate_unused_for_user(user.id)
        raw_token = generate_secure_token()
        await self.email_verification_tokens.create(
            user_id=user.id,
            token_hash=hash_secure_token(raw_token),
            expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.email_verification_token_minutes),
            created_ip=audit_context.ip_address if audit_context else None,
        )
        verify_url = f"{settings.public_frontend_url}/verify-email?token={raw_token}"
        await self.email.send_email_verification(to=user.email, verify_url=verify_url)
        await self.audit.record_event(
            action="user.email_verification.sent",
            actor_user_id=user.id,
            organization_id=None,
            resource_type="user",
            resource_id=user.id,
            request_context=audit_context,
        )

    async def verify_email(
        self,
        raw_token: str,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> UserResponse:
        token_hash = hash_secure_token(raw_token)
        token_record = await self.email_verification_tokens.get_by_hash_for_update(
            token_hash
        )
        if token_record is None:
            raise UnauthorizedError(INVALID_TOKEN_ERROR)

        now = datetime.now(UTC)
        if token_record.used_at is not None or _as_utc(token_record.expires_at) <= now:
            raise UnauthorizedError(INVALID_TOKEN_ERROR)

        user = await self.users.get_by_id(token_record.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError(INVALID_TOKEN_ERROR)

        token_record.used_at = now
        updated = await self.users.mark_email_verified(user.id)
        assert updated is not None
        await self.audit.record_event(
            action="user.email_verified",
            actor_user_id=user.id,
            organization_id=None,
            resource_type="user",
            resource_id=user.id,
            request_context=audit_context,
        )
        return UserResponse.model_validate(updated)

    async def list_sessions(
        self,
        user: User,
        *,
        current_refresh_token: str | None = None,
    ) -> list[SessionResponse]:
        current_jti: str | None = None
        if current_refresh_token:
            try:
                payload = decode_token(current_refresh_token, expected_type="refresh")
                token_record = await self.refresh_tokens.get_by_jti_for_user(
                    str(payload["jti"]),
                    user.id,
                )
                if (
                    token_record is not None
                    and token_record.token_hash
                    == hash_refresh_token(current_refresh_token)
                ):
                    current_jti = token_record.jti
            except UnauthorizedError:
                current_jti = None

        records = await self.refresh_tokens.list_for_user(user.id)
        return [
            refresh_token_to_session(record, current_jti=current_jti)
            for record in records
        ]

    async def revoke_session(
        self,
        user: User,
        session_id: UUID,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        record = await self.refresh_tokens.get_by_id_for_user(session_id, user.id)
        if record is None:
            raise NotFoundError("Session not found")

        await self.refresh_tokens.revoke_token(record.id, reason="session_revoked")
        await self.audit.record_event(
            action="user.session.revoked",
            actor_user_id=user.id,
            organization_id=None,
            resource_type="refresh_token",
            resource_id=record.id,
            request_context=audit_context,
        )

    async def _issue_token_pair(
        self,
        user: User,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> TokenPairResponse:
        refresh_token, _record = await self._create_refresh_token_record(
            user,
            audit_context=audit_context,
        )
        token_pair = self._build_token_pair(user, refresh_token)
        await self.audit.record_event(
            action="user.login.success",
            actor_user_id=user.id,
            organization_id=None,
            resource_type="user",
            resource_id=user.id,
            request_context=audit_context,
        )
        return token_pair

    async def _create_refresh_token_record(
        self,
        user: User,
        *,
        family_id: UUID | None = None,
        audit_context: AuditRequestContext | None = None,
    ) -> tuple[str, RefreshToken]:
        settings = get_settings()
        token_family_id = family_id or uuid4()
        jti = str(uuid4())
        raw_token = create_refresh_token(
            user.id,
            jti=jti,
            family_id=token_family_id,
        )
        record = await self.refresh_tokens.create(
            user_id=user.id,
            family_id=token_family_id,
            token_hash=hash_refresh_token(raw_token),
            jti=jti,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.refresh_token_expire_days),
            created_ip=audit_context.ip_address if audit_context else None,
            created_user_agent=audit_context.user_agent if audit_context else None,
        )
        return raw_token, record

    def _build_token_pair(self, user: User, refresh_token: str) -> TokenPairResponse:
        settings = get_settings()
        access_token = create_access_token(
            user.id,
            extra_claims={"role": user.role.value, "username": user.username},
        )
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def _record_refresh_failure(
        self,
        audit_context: AuditRequestContext | None,
        *,
        user_id: UUID | None = None,
    ) -> None:
        await self.audit.record_event(
            action="user.token.refresh.failure",
            actor_user_id=user_id,
            organization_id=None,
            resource_type="refresh_token",
            resource_id=None,
            request_context=audit_context,
        )
