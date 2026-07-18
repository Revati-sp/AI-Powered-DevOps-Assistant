from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisStatus, AnalysisType
from app.models.provider_config import LLMOperation
from app.models.user import User
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.reviews import ReviewFinding, ReviewRequest, ReviewResponse
from app.services.audit_service import AuditRequestContext, AuditService
from app.services.llm.gateway import LLMGateway
from app.services.llm.prompts import REVIEW_SYSTEM_PROMPT
from app.services.policy_service import PolicyService
from app.services.rbac import OrganizationAuthService, Permission
from app.utils.sanitization import preview_text, sanitize_text

SECRET_RE = re.compile(
    r"(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*['\"]?[^\s'\"]{6,}"
)
LATEST_TAG_RE = re.compile(r"(?i):\s*latest\b|image:\s*\S+:latest\b")


def _line_of(content: str, match_start: int) -> int:
    return content.count("\n", 0, match_start) + 1


def run_static_checks(config_type: str, content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    lines = content.splitlines()

    for match in SECRET_RE.finditer(content):
        findings.append(
            ReviewFinding(
                severity="critical",
                title="Possible hardcoded secret",
                description="A secret-like key/value pattern was detected in the content.",
                recommendation="Remove secrets and load them from a secret manager or CI store.",
                line=_line_of(content, match.start()),
                source="static",
            )
        )

    if LATEST_TAG_RE.search(content):
        findings.append(
            ReviewFinding(
                severity="medium",
                title="Unpinned latest image tag",
                description="Use of the 'latest' tag reduces reproducibility and auditability.",
                recommendation="Pin immutable tags or digests.",
                line=None,
                source="static",
            )
        )

    if config_type == "dockerfile":
        if not re.search(r"(?m)^USER\s+", content):
            findings.append(
                ReviewFinding(
                    severity="high",
                    title="Container may run as root",
                    description="No USER instruction found.",
                    recommendation="Add a non-root USER before CMD/ENTRYPOINT.",
                    line=None,
                    source="static",
                )
            )
        if not re.search(r"(?i)HEALTHCHECK", content):
            findings.append(
                ReviewFinding(
                    severity="low",
                    title="Missing HEALTHCHECK",
                    description="Dockerfile does not define a HEALTHCHECK.",
                    recommendation="Add a HEALTHCHECK for runtime readiness where appropriate.",
                    line=None,
                    source="static",
                )
            )

    if config_type == "kubernetes":
        if re.search(r"(?i)privileged:\s*true", content):
            findings.append(
                ReviewFinding(
                    severity="critical",
                    title="Privileged container",
                    description="privileged: true grants broad host access.",
                    recommendation="Disable privileged mode and drop capabilities.",
                    line=None,
                    source="static",
                )
            )
        if not re.search(r"(?i)resources:", content):
            findings.append(
                ReviewFinding(
                    severity="high",
                    title="Missing resource limits",
                    description="No resources block detected.",
                    recommendation="Set CPU/memory requests and limits.",
                    line=None,
                    source="static",
                )
            )
        if re.search(r"(?i)type:\s*LoadBalancer", content):
            findings.append(
                ReviewFinding(
                    severity="medium",
                    title="Public network exposure risk",
                    description="LoadBalancer service type may expose workloads publicly.",
                    recommendation="Confirm exposure requirements and restrict with firewalls/policies.",
                    line=None,
                    source="static",
                )
            )

    if config_type == "github-actions":
        if re.search(r"(?i)permissions:\s*write-all|contents:\s*write", content):
            findings.append(
                ReviewFinding(
                    severity="high",
                    title="Dangerous workflow permissions",
                    description="Broad write permissions increase supply-chain risk.",
                    recommendation="Use least-privilege permissions scoped to needed resources.",
                    line=None,
                    source="static",
                )
            )
        if re.search(r"(?i)curl .+\|\s*(ba)?sh", content):
            findings.append(
                ReviewFinding(
                    severity="critical",
                    title="Remote script piped to shell",
                    description="Piping curl output to shell is dangerous.",
                    recommendation="Vendor scripts and verify checksums/signatures.",
                    line=None,
                    source="static",
                )
            )

    if config_type == "terraform":
        if re.search(r"(?i)acl\s*=\s*\"public-read\"", content):
            findings.append(
                ReviewFinding(
                    severity="critical",
                    title="Public object storage ACL",
                    description="public-read ACL can expose sensitive data.",
                    recommendation="Use private ACLs and controlled access policies.",
                    line=None,
                    source="static",
                )
            )
        if not re.search(r"(?i)encrypted\s*=\s*true|kms_key", content):
            findings.append(
                ReviewFinding(
                    severity="medium",
                    title="Missing encryption indicators",
                    description="No explicit encryption settings were detected.",
                    recommendation="Enable encryption at rest for stateful resources.",
                    line=None,
                    source="static",
                )
            )

    for idx, line in enumerate(lines, start=1):
        if re.search(r"(?i)USER\s+root\b", line):
            findings.append(
                ReviewFinding(
                    severity="high",
                    title="Explicit root user",
                    description="Configuration sets USER root.",
                    recommendation="Run as a non-root user.",
                    line=idx,
                    source="static",
                )
            )

    return findings


def _policy_to_review_finding(policy_finding: Any) -> ReviewFinding:
    return ReviewFinding(
        severity=policy_finding.severity,
        title=policy_finding.title,
        description=policy_finding.description,
        recommendation=policy_finding.recommendation,
        line=policy_finding.line,
        source="organization_policy",
        rule_key=policy_finding.rule_key,
        policy_pack_id=policy_finding.policy_pack_id,
    )


def _score_from_findings(findings: list[ReviewFinding]) -> int:
    score = 100
    penalties = {
        "info": 1,
        "low": 5,
        "medium": 10,
        "high": 20,
        "critical": 30,
    }
    for finding in findings:
        score -= penalties.get(finding.severity, 5)
    return max(0, min(100, score))


class SecurityReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.artifacts = ArtifactRepository(session)
        self.policy_service = PolicyService(session)
        self.org_auth = OrganizationAuthService(session)
        self.audit = AuditService(session)

    async def review(
        self,
        user: User,
        payload: ReviewRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> ReviewResponse:
        content = sanitize_text(payload.content, max_length=500_000)
        built_in_findings = run_static_checks(payload.type, content)
        organization_policy_findings: list[ReviewFinding] = []
        llm_findings: list[ReviewFinding] = []

        if payload.organization_id and payload.policy_pack_ids:
            await self.org_auth.require_permission(
                payload.organization_id, user.id, Permission.POLICY_READ
            )
            policy_findings = await self.policy_service.evaluate_packs(
                organization_id=payload.organization_id,
                policy_pack_ids=payload.policy_pack_ids,
                config_type=payload.type,
                content=content,
            )
            organization_policy_findings = [
                _policy_to_review_finding(item) for item in policy_findings
            ]

        deterministic_findings = built_in_findings + organization_policy_findings
        summary = (
            f"Static review found {len(built_in_findings)} issue(s) "
            f"and organization policies found {len(organization_policy_findings)} issue(s) "
            f"in {payload.type} configuration."
        )
        improved_content: str | None = None

        try:
            gateway = LLMGateway(self.session)
            prompt = (
                f"Config type: {payload.type}\n"
                f"Static findings: {json.dumps([f.model_dump() for f in deterministic_findings])}\n\n"
                f"CONTENT:\n{content[:100_000]}"
            )
            raw, _provider = await gateway.generate(
                user=user,
                operation=LLMOperation.CONFIGURATION_REVIEW,
                organization_id=payload.organization_id,
                prompt=prompt,
                system_prompt=REVIEW_SYSTEM_PROMPT,
                explicit_provider=payload.provider,
            )
            text = raw.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            data: dict[str, Any] = json.loads(text)
            summary = str(data.get("summary") or summary)
            improved_content = data.get("improved_content")
            for item in data.get("findings") or []:
                finding = ReviewFinding.model_validate({**item, "source": "llm"})
                llm_findings.append(finding)
        except Exception:  # noqa: BLE001
            pass

        all_findings = deterministic_findings + llm_findings
        result = ReviewResponse(
            score=_score_from_findings(deterministic_findings),
            summary=summary,
            findings=all_findings,
            built_in_findings=built_in_findings,
            organization_policy_findings=organization_policy_findings,
            llm_findings=llm_findings,
            improved_content=improved_content
            if isinstance(improved_content, str)
            else None,
        )

        await self.artifacts.create_analysis(
            user_id=user.id,
            analysis_type=AnalysisType.REVIEW,
            input_preview=preview_text(content),
            status=AnalysisStatus.COMPLETED,
            result_json=result.model_dump(mode="json"),
        )
        await self.audit.record_event(
            action="review.completed",
            actor_user_id=user.id,
            organization_id=payload.organization_id,
            resource_type="review",
            resource_id=None,
            request_context=audit_context,
            metadata={
                "config_type": payload.type,
                "finding_count": len(deterministic_findings),
            },
        )
        return result
