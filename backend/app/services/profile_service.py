from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationAppError
from app.core.security import generate_secure_token, hash_secure_token, verify_password
from app.models.user import User
from app.repositories.email_change_token_repository import EmailChangeTokenRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserProfileUpdateRequest, UserResponse
from app.services.audit_service import AuditRequestContext, AuditService
from app.services.email_service import EmailService
from app.services.onboarding_service import OnboardingService
from app.utils.usernames import (
    normalize_display_name,
    validate_avatar_url,
    validate_timezone,
    validate_username,
)

GENERIC_EMAIL_CHANGE_MESSAGE = (
    "If the request is valid, a confirmation email has been sent."
)
INVALID_TOKEN_ERROR = "Invalid or expired token."


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)
        self.email_change_tokens = EmailChangeTokenRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)
        self.audit = AuditService(session)
        self.email = EmailService()
        self.onboarding = OnboardingService(session)

    async def update_profile(
        self,
        user: User,
        payload: UserProfileUpdateRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> UserResponse:
        updates = payload.model_dump(exclude_unset=True)
        if "username" in updates:
            username = validate_username(updates["username"])
            existing = await self.users.get_by_username(username)
            if existing is not None and existing.id != user.id:
                raise ConflictError("Username already taken")
            updates["username"] = username
        if "display_name" in updates:
            updates["display_name"] = normalize_display_name(updates["display_name"])
        if "timezone" in updates:
            updates["timezone"] = validate_timezone(updates["timezone"])
        if "job_title" in updates and updates["job_title"] is not None:
            updates["job_title"] = updates["job_title"].strip() or None
        if "avatar_url" in updates:
            updates["avatar_url"] = validate_avatar_url(updates["avatar_url"])

        changed_fields = [
            field for field, value in updates.items() if getattr(user, field) != value
        ]
        if not changed_fields:
            return UserResponse.model_validate(user)

        updated = await self.users.update_profile(
            user.id, **{field: updates[field] for field in changed_fields}
        )
        assert updated is not None

        if (
            "display_name" in changed_fields and updated.display_name is not None
        ) or "username" in changed_fields:
            await self.onboarding.mark_flag(updated.id, profile_completed=True)

        await self.audit.record_event(
            action="user.profile.updated",
            actor_user_id=updated.id,
            organization_id=None,
            resource_type="user",
            resource_id=updated.id,
            request_context=audit_context,
            metadata={"changed_fields": changed_fields},
        )
        return UserResponse.model_validate(updated)

    async def request_email_change(
        self,
        user: User,
        new_email: str,
        password: str,
        *,
        audit_context: AuditRequestContext | None = None,
        request_ip: str | None = None,
    ) -> str:
        normalized_email = new_email.lower()
        if normalized_email == user.email:
            raise ValidationAppError("New email must differ from your current email.")
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid authentication credentials.")

        existing = await self.users.get_by_email(normalized_email)
        # Do not reveal whether the address is already registered.
        if existing is None:
            settings = get_settings()
            await self.email_change_tokens.invalidate_unused_for_user(user.id)
            raw_token = generate_secure_token()
            await self.email_change_tokens.create(
                user_id=user.id,
                token_hash=hash_secure_token(raw_token),
                new_email=normalized_email,
                expires_at=datetime.now(UTC)
                + timedelta(minutes=settings.email_verification_token_minutes),
                created_ip=request_ip
                or (audit_context.ip_address if audit_context else None),
            )
            confirmation_url = (
                f"{settings.public_frontend_url}/confirm-email-change?token={raw_token}"
            )
            await self.email.send_email_change_confirmation(
                to=normalized_email,
                confirm_url=confirmation_url,
            )
            await self.audit.record_event(
                action="user.email_change.requested",
                actor_user_id=user.id,
                organization_id=None,
                resource_type="user",
                resource_id=user.id,
                request_context=audit_context,
            )
        return GENERIC_EMAIL_CHANGE_MESSAGE

    async def confirm_email_change(
        self,
        raw_token: str,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> UserResponse:
        token_record = await self.email_change_tokens.get_by_hash_for_update(
            hash_secure_token(raw_token)
        )
        if token_record is None:
            raise UnauthorizedError(INVALID_TOKEN_ERROR)

        now = datetime.now(UTC)
        if token_record.used_at is not None or _as_utc(token_record.expires_at) <= now:
            raise UnauthorizedError(INVALID_TOKEN_ERROR)

        user = await self.users.get_by_id(token_record.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError(INVALID_TOKEN_ERROR)
        existing = await self.users.get_by_email(token_record.new_email)
        if existing is not None and existing.id != user.id:
            raise ConflictError("Email unavailable")

        token_record.used_at = now
        updated = await self.users.update_email(user.id, token_record.new_email)
        assert updated is not None
        revoked_count = await self.refresh_tokens.revoke_all_for_user(
            updated.id, reason="email_change"
        )
        await self.audit.record_event(
            action="user.email.changed",
            actor_user_id=updated.id,
            organization_id=None,
            resource_type="user",
            resource_id=updated.id,
            request_context=audit_context,
            metadata={"revoked_count": revoked_count},
        )
        return UserResponse.model_validate(updated)
