from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisStatus, AnalysisType
from app.models.user import User
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.reviews import ReviewFinding, ReviewRequest, ReviewResponse
from app.services.llm.factory import get_llm_provider
from app.services.llm.prompts import REVIEW_SYSTEM_PROMPT
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

    # Capture first USER/root style issues by scanning lines for context.
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
        self.artifacts = ArtifactRepository(session)

    async def review(self, user: User, payload: ReviewRequest) -> ReviewResponse:
        content = sanitize_text(payload.content, max_length=500_000)
        findings = run_static_checks(payload.type, content)
        summary = f"Static review found {len(findings)} issue(s) in {payload.type} configuration."
        improved_content: str | None = None

        try:
            provider = get_llm_provider(payload.provider)
            prompt = (
                f"Config type: {payload.type}\n"
                f"Static findings: {json.dumps([f.model_dump() for f in findings])}\n\n"
                f"CONTENT:\n{content[:100_000]}"
            )
            raw = await provider.generate(prompt, system_prompt=REVIEW_SYSTEM_PROMPT)
            text = raw.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            data: dict[str, Any] = json.loads(text)
            summary = str(data.get("summary") or summary)
            improved_content = data.get("improved_content")
            for item in data.get("findings") or []:
                finding = ReviewFinding.model_validate({**item, "source": "llm"})
                findings.append(finding)
        except Exception:  # noqa: BLE001
            pass

        result = ReviewResponse(
            score=_score_from_findings(findings),
            summary=summary,
            findings=findings,
            improved_content=improved_content
            if isinstance(improved_content, str)
            else None,
        )

        await self.artifacts.create_analysis(
            user_id=user.id,
            analysis_type=AnalysisType.REVIEW,
            input_preview=preview_text(content),
            status=AnalysisStatus.COMPLETED,
            result_json=result.model_dump(),
        )
        return result
