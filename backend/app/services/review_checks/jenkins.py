"""Deterministic Jenkinsfile review checks.

Limitations:
- Does not execute Groovy or build a full AST.
- Uses focused text/pattern matching for declarative and common scripted forms.
- Missing timeout/retry/post are reliability signals, not critical security findings.
- Dynamic Groovy evaluation detection is heuristic only.
"""

from __future__ import annotations

import re

from app.schemas.reviews import ReviewFinding
from app.services.review_checks.common import (
    dedupe_findings,
    finding,
    line_of,
    scan_dangerous_shell,
    scan_hardcoded_secrets,
    scan_latest_and_unpinned_images,
    scan_privileged_and_docker_socket,
    scan_sensitive_paths,
)

AGENT_ANY_RE = re.compile(r"(?i)\bagent\s+any\b")
TIMEOUT_RE = re.compile(r"(?i)\btimeout\s*\(")
RETRY_RE = re.compile(r"(?i)\bretry\s*\(")
POST_RE = re.compile(r"(?i)\bpost\s*\{")
INPUT_RE = re.compile(r"(?i)\binput\s*\(")
WITH_CREDS_RE = re.compile(r"(?i)\bwithCredentials\s*\(")
CREDS_ID_RE = re.compile(r"(?i)credentials\s*\(\s*['\"][^'\"]+['\"]\s*\)")
SECRET_INTERP_RE = re.compile(
    r"(?i)(?:sh|bat|powershell)\s+[\"'][^\"'\n]*\$\{?[A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|API[_-]?KEY|PASSWD)[A-Z0-9_]*\}?"
)
ECHO_SECRET_RE = re.compile(
    r"(?i)(?:echo|printenv|env)\s+.*\$\{?[A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|API[_-]?KEY|PASSWD)[A-Z0-9_]*\}?"
)
EVAL_RE = re.compile(r"(?i)\b(?:evaluate|Eval\.me|load\s*\(|GroovyShell)\b")
DEPLOY_CMD_RE = re.compile(
    r"(?i)\b(?:kubectl\s+apply|helm\s+upgrade|terraform\s+apply|ansible-playbook)\b"
)
DOCKER_IMAGE_RE = re.compile(
    r"(?i)(?:docker\s+(?:pull|run)\s+|image\s+['\"])([^\s'\"]+)"
)


def _check_agent_any(content: str) -> list[ReviewFinding]:
    match = AGENT_ANY_RE.search(content)
    if not match:
        return []
    return [
        finding(
            severity="info",
            title="Unrestricted agent any",
            description=(
                "`agent any` allows the pipeline to run on any available executor. "
                "Treat as a reliability/isolation signal, not a critical vulnerability."
            ),
            recommendation="Prefer labeled agents that match required tools and trust boundaries.",
            line=line_of(content, match.start()),
            rule_key="jenkins_agent_any",
        )
    ]


def _check_reliability_controls(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    if "pipeline" in content.lower() and not TIMEOUT_RE.search(content):
        findings.append(
            finding(
                severity="low",
                title="Missing pipeline timeout",
                description="No timeout(...) option was detected in the Jenkinsfile.",
                recommendation="Add a timeout to prevent runaway builds.",
                rule_key="jenkins_missing_timeout",
            )
        )
    if "pipeline" in content.lower() and not POST_RE.search(content):
        findings.append(
            finding(
                severity="info",
                title="Missing post cleanup block",
                description="No post { ... } cleanup block was detected.",
                recommendation="Add post cleanup for workspace and credential hygiene.",
                rule_key="jenkins_missing_post",
            )
        )
    if "pipeline" in content.lower() and not RETRY_RE.search(content):
        # informational only — not always required
        pass
    return findings


def _check_credentials(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    findings.extend(scan_hardcoded_secrets(content))

    # Proper credentials('id') / withCredentials should not be treated as literal secrets.
    # Additional interpolation risks:
    for match in SECRET_INTERP_RE.finditer(content):
        findings.append(
            finding(
                severity="high",
                title="Secret interpolated into shell step",
                description=(
                    "A secret-like environment variable appears interpolated into a "
                    "shell/bat/powershell step and may leak via process listings or logs."
                ),
                recommendation=(
                    "Prefer withCredentials bindings and avoid echoing secret values."
                ),
                line=line_of(content, match.start()),
                rule_key="jenkins_secret_interpolation",
            )
        )

    for match in ECHO_SECRET_RE.finditer(content):
        findings.append(
            finding(
                severity="high",
                title="Possible credential logging",
                description="A command may print environment variables containing secrets.",
                recommendation="Never echo credentials; rely on masked bindings.",
                line=line_of(content, match.start()),
                rule_key="jenkins_secret_logging",
            )
        )

    # Note presence of withCredentials as healthy signal — no finding.
    _ = WITH_CREDS_RE.search(content) or CREDS_ID_RE.search(content)
    return findings


def _check_deploy_without_approval(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    deploy = DEPLOY_CMD_RE.search(content)
    if deploy and not INPUT_RE.search(content):
        findings.append(
            finding(
                severity="medium",
                title="Deployment without input approval",
                description=(
                    "A deployment or infrastructure apply command was found without an "
                    "obvious input(...) approval step."
                ),
                recommendation="Require an input approval stage before production changes.",
                line=line_of(content, deploy.start()),
                rule_key="jenkins_deploy_without_approval",
            )
        )
    return findings


def _check_dynamic_groovy(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    match = EVAL_RE.search(content)
    if match:
        findings.append(
            finding(
                severity="high",
                title="Dynamic Groovy evaluation",
                description=(
                    "Dynamic Groovy evaluation or script loading was detected. "
                    "This increases script-approval and remote-code risk."
                ),
                recommendation=(
                    "Avoid evaluate/load of untrusted scripts; use approved shared libraries."
                ),
                line=line_of(content, match.start()),
                rule_key="jenkins_dynamic_groovy",
            )
        )
    return findings


def check_jenkins(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []

    stripped = content.strip()
    if (
        stripped
        and "pipeline" not in stripped.lower()
        and "node(" not in stripped.lower()
    ):
        findings.append(
            finding(
                severity="info",
                title="Unrecognized Jenkins pipeline structure",
                description=(
                    "Content does not clearly look like a declarative pipeline or "
                    "common scripted node(...) form. Checks still ran on text patterns."
                ),
                recommendation="Provide a standard Jenkinsfile for more accurate review.",
                rule_key="jenkins_unrecognized_syntax",
            )
        )

    findings.extend(_check_credentials(content))
    findings.extend(scan_dangerous_shell(content))
    findings.extend(scan_latest_and_unpinned_images(content))
    findings.extend(scan_privileged_and_docker_socket(content))
    findings.extend(scan_sensitive_paths(content))
    findings.extend(_check_agent_any(content))
    findings.extend(_check_reliability_controls(content))
    findings.extend(_check_deploy_without_approval(content))
    findings.extend(_check_dynamic_groovy(content))

    # Docker image mutable tags via docker run/pull
    for match in DOCKER_IMAGE_RE.finditer(content):
        image = match.group(1)
        if image.endswith(":latest"):
            findings.append(
                finding(
                    severity="medium",
                    title="Unpinned latest image tag",
                    description=f"Docker usage references mutable image '{image}'.",
                    recommendation="Pin immutable tags or digests.",
                    line=line_of(content, match.start()),
                    rule_key="forbid_latest_image_tag",
                )
            )

    return dedupe_findings(findings)
