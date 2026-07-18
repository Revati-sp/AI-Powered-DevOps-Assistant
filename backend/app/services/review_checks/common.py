from __future__ import annotations

import re

from app.schemas.reviews import ReviewFinding

ENV_REF_RE = re.compile(
    r"^\$\{?[A-Za-z_][A-Za-z0-9_]*\}?$|"
    r"^\$\{\{\s*secrets\.[^}]+\}\}$|"
    r"^\$\{\{\s*env\.[^}]+\}\}$|"
    r"^credentials\(['\"][^'\"]+['\"]\)$",
    re.I,
)

SECRET_KEY_RE = re.compile(
    r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?key|token|private[_-]?key)\b"
)

PIPE_TO_SHELL_RE = re.compile(r"(?i)\b(curl|wget)\b.+\|\s*(ba)?sh\b")
RM_RF_ROOT_RE = re.compile(r"(?i)\brm\s+(-[^\s]*\s+)*(/|/\*|/\.\.)")
CHMOD_777_RE = re.compile(r"(?i)\bchmod\s+-R\s+777\b")
DOCKER_LOGIN_INLINE_RE = re.compile(r"(?i)\bdocker\s+login\b.+(?:-p|--password)\s+\S+")
KUBECTL_APPLY_RE = re.compile(r"(?i)\bkubectl\s+apply\b")
TF_AUTO_APPROVE_RE = re.compile(r"(?i)\bterraform\s+apply\b.*-auto-approve")
TF_DESTROY_RE = re.compile(r"(?i)\bterraform\s+destroy\b")
UNPINNED_IMAGE_RE = re.compile(
    r"(?im)^[ \t]*image:[ \t]*([A-Za-z0-9][A-Za-z0-9._/-]*)[ \t]*$",
)
PRIVILEGED_RE = re.compile(r"(?i)\bprivileged\s*[:=]\s*true\b")
DOCKER_SOCKET_RE = re.compile(r"(?i)/var/run/docker\.sock")
SENSITIVE_PATH_RE = re.compile(
    r"(?i)(?:^|[\s\"'/])(\.env(?:\.\w+)?|id_rsa|id_ed25519|\.aws/credentials|"
    r"\.kube/config|\.docker/config\.json|\.git-credentials)(?:$|[\s\"'/])"
)
PRINT_ENV_RE = re.compile(
    r"(?i)\b(?:env|printenv|echo\s+\$\{?(?:PASSWORD|SECRET|TOKEN|API_KEY))"
)


def line_of(content: str, match_start: int) -> int:
    return content.count("\n", 0, match_start) + 1


def finding(
    *,
    severity: str,
    title: str,
    description: str,
    recommendation: str,
    line: int | None = None,
    rule_key: str | None = None,
) -> ReviewFinding:
    return ReviewFinding(
        severity=severity,  # type: ignore[arg-type]
        title=title,
        description=description,
        recommendation=recommendation,
        line=line,
        source="static",
        rule_key=rule_key,
    )


def looks_like_env_reference(value: str) -> bool:
    cleaned = value.strip().strip("'\"")
    if not cleaned:
        return False
    if ENV_REF_RE.match(cleaned):
        return True
    # GitLab/Jenkins common expansions
    if cleaned.startswith("$") and " " not in cleaned:
        return True
    return False


def scan_hardcoded_secrets(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    for match in re.finditer(
        r"(?i)(password|passwd|secret|api[_-]?key|access[_-]?key|token|"
        r"private[_-]?key)\s*[:=]\s*['\"]?([^\s'\"]{6,})",
        content,
    ):
        value = match.group(2)
        if looks_like_env_reference(value):
            continue
        if value.lower() in {"changeme", "placeholder", "redacted", "xxxxx"}:
            continue
        findings.append(
            finding(
                severity="critical",
                title="Possible hardcoded secret",
                description=(
                    "A secret-like key/value pattern was detected. "
                    "Environment or credential-store references were excluded."
                ),
                recommendation=(
                    "Remove secrets from pipeline files and load them from "
                    "the CI credential store or secret manager."
                ),
                line=line_of(content, match.start()),
                rule_key="ci_hardcoded_secret",
            )
        )
    return findings


def scan_dangerous_shell(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    checks: list[tuple[re.Pattern[str], str, str, str, str]] = [
        (
            PIPE_TO_SHELL_RE,
            "critical",
            "Remote script piped to shell",
            "Piping curl/wget output to a shell is dangerous.",
            "Vendor scripts and verify checksums or signatures before execution.",
        ),
        (
            RM_RF_ROOT_RE,
            "critical",
            "Destructive recursive delete",
            "A recursive force delete targeting the filesystem root was detected.",
            "Remove destructive cleanup from CI and scope deletes carefully.",
        ),
        (
            CHMOD_777_RE,
            "high",
            "World-writable recursive permissions",
            "chmod -R 777 weakens filesystem permissions.",
            "Use least-privilege modes appropriate for the workload.",
        ),
        (
            DOCKER_LOGIN_INLINE_RE,
            "critical",
            "Docker login with inline password",
            "Inline registry passwords may expose credentials in logs and history.",
            "Use the CI credential helper or a secret-mounted auth config.",
        ),
        (
            TF_DESTROY_RE,
            "critical",
            "Terraform destroy in pipeline",
            "terraform destroy can remove infrastructure.",
            "Require human approval and restrict destroy to controlled workflows.",
        ),
        (
            TF_AUTO_APPROVE_RE,
            "high",
            "Terraform apply with auto-approve",
            "Auto-approved Terraform apply skips interactive review.",
            "Require plan review and manual approval before apply.",
        ),
        (
            KUBECTL_APPLY_RE,
            "medium",
            "kubectl apply without review context",
            "Direct kubectl apply was detected in the pipeline content.",
            "Treat apply as human-approved remediation; prefer reviewable diffs.",
        ),
    ]
    for pattern, severity, title, description, recommendation in checks:
        match = pattern.search(content)
        if match:
            findings.append(
                finding(
                    severity=severity,
                    title=title,
                    description=description,
                    recommendation=recommendation,
                    line=line_of(content, match.start()),
                    rule_key="ci_dangerous_shell",
                )
            )
    return findings


def scan_latest_and_unpinned_images(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    if re.search(r"(?i):\s*latest\b|image:\s*\S+:latest\b", content):
        findings.append(
            finding(
                severity="medium",
                title="Unpinned latest image tag",
                description="Use of the 'latest' tag reduces reproducibility and auditability.",
                recommendation="Pin immutable tags or digests.",
                rule_key="forbid_latest_image_tag",
            )
        )
    for match in UNPINNED_IMAGE_RE.finditer(content):
        image = match.group(1)
        if ":" in image or "@sha256:" in image:
            continue
        # Skip variables
        if looks_like_env_reference(image) or "$" in image:
            continue
        findings.append(
            finding(
                severity="low",
                title="Unversioned container image",
                description=f"Image '{image}' has no tag or digest.",
                recommendation="Pin a version tag or digest for reproducible builds.",
                line=line_of(content, match.start()),
                rule_key="ci_unpinned_image",
            )
        )
    return findings


def scan_privileged_and_docker_socket(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    match = PRIVILEGED_RE.search(content)
    if match:
        findings.append(
            finding(
                severity="critical",
                title="Privileged container or runner",
                description="privileged: true grants broad host access.",
                recommendation="Disable privileged mode unless absolutely required.",
                line=line_of(content, match.start()),
                rule_key="forbid_privileged_container",
            )
        )
    sock = DOCKER_SOCKET_RE.search(content)
    if sock:
        findings.append(
            finding(
                severity="high",
                title="Docker socket mount",
                description="Mounting /var/run/docker.sock can expose the host Docker daemon.",
                recommendation="Avoid socket mounts; use isolated builders or DinD carefully.",
                line=line_of(content, sock.start()),
                rule_key="ci_docker_socket",
            )
        )
    if re.search(r"(?i)\bdind\b|docker:dind", content):
        findings.append(
            finding(
                severity="medium",
                title="Docker-in-Docker pattern",
                description="Docker-in-Docker increases privilege and escape risk.",
                recommendation="Prefer rootless builders or remote build services.",
                rule_key="ci_dind",
            )
        )
    return findings


def scan_sensitive_paths(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    for match in SENSITIVE_PATH_RE.finditer(content):
        findings.append(
            finding(
                severity="high",
                title="Sensitive path referenced",
                description=(
                    f"Reference to '{match.group(1)}' may expose credentials or secrets "
                    "via artifacts or scripts."
                ),
                recommendation="Exclude secret files from artifacts and never print them.",
                line=line_of(content, match.start()),
                rule_key="ci_sensitive_path",
            )
        )
    return findings


def dedupe_findings(findings: list[ReviewFinding]) -> list[ReviewFinding]:
    seen: set[tuple[str, str, int | None]] = set()
    unique: list[ReviewFinding] = []
    for item in findings:
        key = (item.title, item.description, item.line)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
