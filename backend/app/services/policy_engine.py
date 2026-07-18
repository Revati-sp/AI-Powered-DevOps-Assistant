from __future__ import annotations

import re
from uuid import UUID

from app.models.policy import PolicyRule
from app.schemas.policies import PolicyFinding

LATEST_TAG_RE = re.compile(r"(?i):\s*latest\b|image:\s*\S+:latest\b")
IMAGE_DIGEST_RE = re.compile(r"@sha256:[a-f0-9]{64}")
UNPINNED_GHA_RE = re.compile(r"uses:\s*[^\s@]+@[^#\n]+(?<!@sha256:[a-f0-9]{64})")


def _line_of(content: str, match_start: int) -> int:
    return content.count("\n", 0, match_start) + 1


def _matches_resource(rule: PolicyRule, config_type: str) -> bool:
    if rule.resource_type == "general":
        return True
    return rule.resource_type == config_type


def _finding(
    rule: PolicyRule,
    *,
    policy_pack_id: UUID,
    title: str,
    description: str,
    recommendation: str | None = None,
    line: int | None = None,
) -> PolicyFinding:
    return PolicyFinding(
        rule_key=rule.rule_key,
        severity=rule.severity,  # type: ignore[arg-type]
        title=title,
        description=description,
        recommendation=recommendation or rule.remediation or "Review and remediate.",
        policy_pack_id=policy_pack_id,
        line=line,
    )


def evaluate_rule(
    rule: PolicyRule,
    *,
    config_type: str,
    content: str,
    policy_pack_id: UUID,
) -> list[PolicyFinding]:
    if not rule.is_enabled or not _matches_resource(rule, config_type):
        return []

    key = rule.rule_key
    config = rule.configuration_json or {}
    findings: list[PolicyFinding] = []

    if key == "require_non_root_container":
        if config_type == "dockerfile" and not re.search(r"(?m)^USER\s+", content):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Non-root container required",
                    description="No USER instruction found in Dockerfile.",
                )
            )
        if config_type == "kubernetes" and re.search(
            r"(?i)runAsNonRoot:\s*false", content
        ):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Container runs as root",
                    description="runAsNonRoot is explicitly false.",
                )
            )
        if config_type == "kubernetes" and not re.search(
            r"(?i)runAsNonRoot:\s*true", content
        ):
            if re.search(r"(?i)kind:\s*Deployment|kind:\s*Pod", content):
                findings.append(
                    _finding(
                        rule,
                        policy_pack_id=policy_pack_id,
                        title="Non-root security context missing",
                        description="No runAsNonRoot: true found in Kubernetes manifest.",
                    )
                )

    elif key == "forbid_privileged_container":
        if re.search(r"(?i)privileged:\s*true", content):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Privileged container forbidden",
                    description="privileged: true grants broad host access.",
                )
            )

    elif key == "forbid_latest_image_tag":
        # Applies whenever content matches (dockerfile/k8s/CI/general packs).
        match = LATEST_TAG_RE.search(content)
        if match:
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Mutable image tag is forbidden",
                    description="The container image uses the latest tag.",
                    recommendation="Use a versioned image tag or immutable digest.",
                    line=_line_of(content, match.start()),
                )
            )

    elif key == "require_resource_limits":
        if config_type == "kubernetes" and not re.search(r"(?i)resources:", content):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Resource limits required",
                    description="No resources block detected.",
                )
            )

    elif key == "require_liveness_probe":
        if config_type == "kubernetes" and not re.search(
            r"(?i)livenessProbe:", content
        ):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Liveness probe required",
                    description="No livenessProbe found.",
                )
            )

    elif key == "require_readiness_probe":
        if config_type == "kubernetes" and not re.search(
            r"(?i)readinessProbe:", content
        ):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Readiness probe required",
                    description="No readinessProbe found.",
                )
            )

    elif key == "require_image_digest":
        if config_type in {"dockerfile", "kubernetes"} and not IMAGE_DIGEST_RE.search(
            content
        ):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Image digest required",
                    description="No @sha256 digest found for container images.",
                )
            )

    elif key == "allowed_container_registries":
        registries = config.get("registries") or []
        for match in re.finditer(
            r"(?i)(?:image:\s*|FROM\s+)(['\"]?)([^\s'\"/:]+(?:/[^\s'\"/:]+)*)",
            content,
        ):
            image_ref = match.group(2)
            if not any(image_ref.startswith(registry) for registry in registries):
                findings.append(
                    _finding(
                        rule,
                        policy_pack_id=policy_pack_id,
                        title="Disallowed container registry",
                        description=f"Image reference '{image_ref}' is not in the allow list.",
                        line=_line_of(content, match.start()),
                    )
                )

    elif key == "forbid_host_network":
        if re.search(r"(?i)hostNetwork:\s*true", content):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Host networking forbidden",
                    description="hostNetwork: true was detected.",
                )
            )

    elif key == "forbid_host_path":
        if re.search(r"(?i)hostPath:", content):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Host path volume forbidden",
                    description="hostPath volume mount detected.",
                )
            )

    elif key == "required_kubernetes_labels":
        if config_type != "kubernetes":
            return findings
        for label in config.get("labels") or []:
            if not re.search(rf"(?m)^\s*{re.escape(label)}:", content):
                findings.append(
                    _finding(
                        rule,
                        policy_pack_id=policy_pack_id,
                        title="Required Kubernetes label missing",
                        description=f"Required label '{label}' was not found.",
                    )
                )

    elif key == "forbid_github_write_all":
        if re.search(r"(?i)permissions:\s*write-all|contents:\s*write", content):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Dangerous workflow permissions",
                    description="Broad write permissions increase supply-chain risk.",
                )
            )

    elif key == "require_pinned_github_actions":
        for match in re.finditer(r"(?m)^\s*-\s*uses:\s*(.+)$", content):
            uses_value = match.group(1).strip()
            if "@" not in uses_value or UNPINNED_GHA_RE.search(f"uses: {uses_value}"):
                if (
                    "@main" in uses_value
                    or "@master" in uses_value
                    or ":latest" in uses_value
                ):
                    findings.append(
                        _finding(
                            rule,
                            policy_pack_id=policy_pack_id,
                            title="Unpinned GitHub Action",
                            description=f"Action '{uses_value}' is not pinned to an immutable ref.",
                            line=_line_of(content, match.start()),
                        )
                    )
                elif re.search(r"@[vV]\d+(?:\.\d+)*$", uses_value):
                    findings.append(
                        _finding(
                            rule,
                            policy_pack_id=policy_pack_id,
                            title="Floating GitHub Action tag",
                            description=f"Action '{uses_value}' uses a mutable version tag.",
                            line=_line_of(content, match.start()),
                        )
                    )

    elif key == "require_terraform_encryption":
        if config_type == "terraform" and not re.search(
            r"(?i)encrypted\s*=\s*true|kms_key", content
        ):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Encryption required",
                    description="No explicit encryption settings were detected.",
                )
            )

    elif key == "forbid_public_cloud_storage":
        if re.search(
            r"(?i)acl\s*=\s*\"public-read\"|public_access_block\s*=\s*false", content
        ):
            findings.append(
                _finding(
                    rule,
                    policy_pack_id=policy_pack_id,
                    title="Public cloud storage forbidden",
                    description="Public object storage configuration detected.",
                )
            )

    return findings


def evaluate_policy_rules(
    rules: list[PolicyRule],
    *,
    config_type: str,
    content: str,
    policy_pack_id: UUID,
) -> list[PolicyFinding]:
    findings: list[PolicyFinding] = []
    for rule in rules:
        findings.extend(
            evaluate_rule(
                rule,
                config_type=config_type,
                content=content,
                policy_pack_id=policy_pack_id,
            )
        )
    return findings


def has_critical_findings(findings: list[PolicyFinding]) -> bool:
    return any(f.severity == "critical" for f in findings)
