from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SentEmail:
    to: str
    subject: str
    body_text: str
    body_html: str | None = None


class EmailService:
    """Send transactional email via SMTP when configured, otherwise log to console."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._outbox: list[SentEmail] = []

    @property
    def outbox(self) -> list[SentEmail]:
        return list(self._outbox)

    def clear_outbox(self) -> None:
        self._outbox.clear()

    async def send(
        self,
        *,
        to: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> None:
        message = SentEmail(
            to=to,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
        )
        self._outbox.append(message)

        if not self.settings.email_enabled:
            logger.info(
                "Email disabled; skipped delivery to=%s subject=%s",
                to,
                subject,
            )
            return

        if self._smtp_configured():
            await self._send_smtp(message)
        else:
            logger.info(
                "Email (console): to=%s subject=%s body=%s",
                to,
                subject,
                body_text,
            )

    async def send_password_reset(self, *, to: str, reset_url: str) -> None:
        subject = "Reset your password"
        body_text = (
            "A password reset was requested for your account.\n\n"
            f"Reset your password using this link (expires soon):\n{reset_url}\n\n"
            "If you did not request this, you can ignore this email."
        )
        await self.send(to=to, subject=subject, body_text=body_text)

    async def send_email_verification(self, *, to: str, verify_url: str) -> None:
        subject = "Verify your email address"
        body_text = (
            "Please verify your email address using the link below:\n\n"
            f"{verify_url}\n\n"
            "If you did not create an account, you can ignore this email."
        )
        await self.send(to=to, subject=subject, body_text=body_text)

    async def send_organization_invitation(
        self,
        *,
        to: str,
        invite_url: str,
        organization_name: str,
        role: str,
    ) -> None:
        subject = f"Invitation to join {organization_name}"
        body_text = (
            f"You have been invited to join {organization_name} as {role}.\n\n"
            f"Accept the invitation:\n{invite_url}\n\n"
            "If you were not expecting this invitation, you can ignore this email."
        )
        await self.send(to=to, subject=subject, body_text=body_text)

    def _smtp_configured(self) -> bool:
        return bool(self.settings.smtp_host and self.settings.smtp_from_email)

    async def _send_smtp(self, message: SentEmail) -> None:
        email = EmailMessage()
        email["From"] = self.settings.smtp_from_email
        email["To"] = message.to
        email["Subject"] = message.subject
        email.set_content(message.body_text)
        if message.body_html:
            email.add_alternative(message.body_html, subtype="html")

        try:
            with smtplib.SMTP(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=30,
            ) as smtp:
                if self.settings.smtp_use_tls:
                    smtp.starttls()
                if self.settings.smtp_username:
                    smtp.login(
                        self.settings.smtp_username,
                        self.settings.smtp_password,
                    )
                smtp.send_message(email)
        except Exception:
            logger.exception(
                "Failed to send email to=%s subject=%s",
                message.to,
                message.subject,
            )
            raise
