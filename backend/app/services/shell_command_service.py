from __future__ import annotations

import json
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_artifact import ArtifactType
from app.models.user import User
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.generators import ShellCommandRequest, ShellCommandResponse
from app.services.audit_service import AuditRequestContext
from app.services.generator_artifact_helper import apply_generator_policies_and_save
from app.services.llm.factory import get_llm_provider
from app.services.llm.prompts import SHELL_COMMAND_SYSTEM_PROMPT
from app.utils.command_risk import classify_command_risk
from app.utils.sanitization import sanitize_text


def _heuristic_command(payload: ShellCommandRequest) -> tuple[str, str]:
    request = payload.request.lower()
    if "larger than 1" in request and "/var" in request:
        return (
            "find /var -type f -size +1G 2>/dev/null",
            "Finds files larger than 1GB under /var without modifying anything.",
        )
    if "disk" in request and "usage" in request:
        return "df -h", "Shows mounted filesystem disk usage."
    if "listening" in request and "port" in request:
        return "ss -tulpn", "Lists listening TCP/UDP sockets."
    if "docker" in request and "ps" in request:
        return "docker ps --format 'table {{.ID}}\\t{{.Names}}\\t{{.Status}}'", (
            "Lists running containers in a readable table."
        )
    return (
        "echo 'No deterministic command matched; refine your request or review AI output'",
        "Fallback placeholder when no safe heuristic match is available.",
    )


class ShellCommandService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.artifacts = ArtifactRepository(session)

    async def generate(
        self,
        user: User,
        payload: ShellCommandRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> ShellCommandResponse:
        request = sanitize_text(payload.request, max_length=2000)
        command, explanation = _heuristic_command(payload)

        try:
            provider = get_llm_provider(payload.provider)
            prompt = (
                f"OS={payload.operating_system} shell={payload.shell}\n"
                f"Request: {request}\n"
                "Return a single safe command as JSON."
            )
            raw = await provider.generate(
                prompt, system_prompt=SHELL_COMMAND_SYSTEM_PROMPT
            )
            text = raw.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            data = json.loads(text)
            command = str(data.get("command") or command).strip()
            explanation = str(data.get("explanation") or explanation).strip()
        except Exception:  # noqa: BLE001
            pass

        risk = classify_command_risk(command)
        result = ShellCommandResponse(
            command=command,
            explanation=explanation,
            risk_level=risk.risk_level,
            warnings=risk.warnings,
            requires_confirmation=risk.requires_confirmation,
        )

        policy_findings, saved_artifact_id = await apply_generator_policies_and_save(
            self.session,
            user,
            payload,
            artifact_type=ArtifactType.COMMAND,
            content=result.command,
            default_name="shell-command",
            metadata=result.model_dump(
                exclude={"command", "policy_findings", "saved_artifact_id"}
            ),
            audit_context=audit_context,
        )
        result.policy_findings = policy_findings
        result.saved_artifact_id = saved_artifact_id

        if not payload.save_artifact:
            await self.artifacts.create_artifact(
                user_id=user.id,
                artifact_type=ArtifactType.COMMAND,
                name="shell-command",
                content=result.command,
                metadata_json=result.model_dump(
                    exclude={"command", "policy_findings", "saved_artifact_id"}
                ),
            )
        return result
