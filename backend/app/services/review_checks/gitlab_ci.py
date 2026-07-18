"""Deterministic GitLab CI (.gitlab-ci.yml) review checks.

Limitations:
- Does not fetch remote `include:` sources.
- Uses YAML safe-load when parseable; otherwise falls back to text patterns.
- Branch/environment protections are best-effort heuristics only.
"""

from __future__ import annotations

from typing import Any

import yaml

from app.schemas.reviews import ReviewFinding
from app.services.review_checks.common import (
    dedupe_findings,
    finding,
    line_of,
    looks_like_env_reference,
    scan_dangerous_shell,
    scan_hardcoded_secrets,
    scan_latest_and_unpinned_images,
    scan_privileged_and_docker_socket,
    scan_sensitive_paths,
)

REMOTE_INCLUDE_RE = __import__("re").compile(
    r"(?i)include:\s*\n(?:[^\n]*\n)*?\s*-\s*remote:\s*['\"]?([^\s'\"]+)",
)
UNPINNED_REMOTE_RE = __import__("re").compile(
    r"(?i)remote:\s*['\"]?(https?://[^\s'\"]+)['\"]?",
)


def _safe_load_yaml(content: str) -> Any | None:
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return None
    return data


def _iter_job_dicts(data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    reserved = {
        "stages",
        "variables",
        "default",
        "include",
        "workflow",
        "image",
        "services",
        "before_script",
        "after_script",
        "cache",
        "pages",
    }
    jobs: list[tuple[str, dict[str, Any]]] = []
    for key, value in data.items():
        if key.startswith(".") or key in reserved:
            continue
        if isinstance(value, dict):
            jobs.append((str(key), value))
    return jobs


def _job_has_restriction(job: dict[str, Any]) -> bool:
    rules = job.get("rules")
    if isinstance(rules, list) and rules:
        return True
    only = job.get("only")
    if only:
        return True
    except_cfg = job.get("except")
    if except_cfg:
        return True
    if job.get("environment"):
        return True
    when = str(job.get("when") or "").lower()
    if when in {"manual", "delayed"}:
        return True
    return False


def _check_includes(content: str, data: Any) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    includes: list[Any] = []
    if isinstance(data, dict) and "include" in data:
        raw = data["include"]
        if isinstance(raw, list):
            includes = raw
        elif isinstance(raw, (dict, str)):
            includes = [raw]

    for item in includes:
        remote: str | None = None
        ref: str | None = None
        if isinstance(item, str) and item.startswith("http"):
            remote = item
        elif isinstance(item, dict):
            remote = item.get("remote") if isinstance(item.get("remote"), str) else None
            ref = item.get("ref") if isinstance(item.get("ref"), str) else None
            project = item.get("project")
            if project and not ref:
                findings.append(
                    finding(
                        severity="medium",
                        title="Unpinned GitLab include",
                        description=(
                            "A project include does not pin a stable `ref`. "
                            "Remote includes are not fetched during review."
                        ),
                        recommendation="Pin includes to a tag, commit SHA, or immutable ref.",
                        rule_key="gitlab_unpinned_include",
                    )
                )
        if remote:
            # Treat bare remote URLs without version query/fragment as unpinned.
            if "@" not in remote and "ref=" not in remote and not ref:
                match = UNPINNED_REMOTE_RE.search(content)
                findings.append(
                    finding(
                        severity="medium",
                        title="Unpinned remote include",
                        description=(
                            f"Remote include '{remote}' appears unpinned. "
                            "Remote includes are treated as external dependencies "
                            "and are not fetched during review."
                        ),
                        recommendation="Pin remote includes to an immutable version or checksummed artifact.",
                        line=line_of(content, match.start()) if match else None,
                        rule_key="gitlab_unpinned_remote_include",
                    )
                )
    return findings


def _check_deploy_jobs(jobs: list[tuple[str, dict[str, Any]]]) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    for name, job in jobs:
        stage = str(job.get("stage") or "").lower()
        is_deploy = "deploy" in name.lower() or stage == "deploy"
        if not is_deploy:
            script = job.get("script")
            script_text = (
                "\n".join(script) if isinstance(script, list) else str(script or "")
            )
            if not __import__("re").search(
                r"(?i)\b(kubectl\s+apply|helm\s+upgrade|terraform\s+apply|deploy)\b",
                script_text,
            ):
                continue
            is_deploy = True
        if is_deploy and not _job_has_restriction(job):
            findings.append(
                finding(
                    severity="medium",
                    title="Deployment job without branch or manual restriction",
                    description=(
                        f"Job '{name}' appears to deploy without obvious `rules`/`only`, "
                        "environment, or `when: manual` protections. "
                        "This does not prove branch protection is absent in GitLab settings."
                    ),
                    recommendation=(
                        "Restrict deploy jobs with rules, environments, and manual approval "
                        "for production."
                    ),
                    rule_key="gitlab_unrestricted_deploy",
                )
            )
    return findings


def _check_artifacts(
    jobs: list[tuple[str, dict[str, Any]]], content: str
) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    findings.extend(scan_sensitive_paths(content))
    for name, job in jobs:
        artifacts = job.get("artifacts")
        if not isinstance(artifacts, dict):
            continue
        paths = artifacts.get("paths") or []
        if isinstance(paths, list):
            for path in paths:
                if not isinstance(path, str):
                    continue
                if path.strip() in {".", "./", "**/*", "*"}:
                    findings.append(
                        finding(
                            severity="medium",
                            title="Broad artifact path",
                            description=(
                                f"Job '{name}' publishes a very broad artifact path '{path}'."
                            ),
                            recommendation="Limit artifacts to explicit build outputs.",
                            rule_key="gitlab_broad_artifacts",
                        )
                    )
        expire = artifacts.get("expire_in")
        if expire is None and paths:
            findings.append(
                finding(
                    severity="info",
                    title="Artifact retention not set",
                    description=(
                        f"Job '{name}' defines artifacts without `expire_in`."
                    ),
                    recommendation="Set expire_in to limit retention of build outputs.",
                    rule_key="gitlab_artifact_retention",
                )
            )
    return findings


def _check_token_exposure(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    for match in __import__("re").finditer(
        r"(?i)(echo|printenv|env)\s+.*\b(CI_JOB_TOKEN|CI_DEPLOY_PASSWORD|CI_REGISTRY_PASSWORD)\b",
        content,
    ):
        findings.append(
            finding(
                severity="high",
                title="Built-in token may be printed",
                description="A high-privilege GitLab CI token appears in a print/echo command.",
                recommendation="Never print CI tokens; mask variables and avoid debug dumps.",
                line=line_of(content, match.start()),
                rule_key="gitlab_token_logging",
            )
        )
    # Inline use of job token in curl without masking context is informational
    for match in __import__("re").finditer(
        r"(?i)curl\b.+\b\$CI_JOB_TOKEN\b",
        content,
    ):
        findings.append(
            finding(
                severity="low",
                title="CI_JOB_TOKEN used in script",
                description="CI_JOB_TOKEN is a privileged built-in token used in a script.",
                recommendation="Scope token usage narrowly and avoid leaking it via logs or artifacts.",
                line=line_of(content, match.start()),
                rule_key="gitlab_job_token_use",
            )
        )
    return findings


def check_gitlab_ci(content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    data = _safe_load_yaml(content)

    if data is None and content.strip():
        findings.append(
            finding(
                severity="high",
                title="Invalid GitLab CI YAML",
                description="The configuration could not be parsed as YAML.",
                recommendation="Fix YAML syntax before relying on pipeline behavior.",
                rule_key="gitlab_invalid_yaml",
            )
        )

    findings.extend(scan_hardcoded_secrets(content))
    findings.extend(scan_dangerous_shell(content))
    findings.extend(scan_latest_and_unpinned_images(content))
    findings.extend(scan_privileged_and_docker_socket(content))
    findings.extend(_check_token_exposure(content))

    if isinstance(data, dict):
        findings.extend(_check_includes(content, data))
        jobs = _iter_job_dicts(data)
        findings.extend(_check_deploy_jobs(jobs))
        findings.extend(_check_artifacts(jobs, content))

        variables = data.get("variables")
        if isinstance(variables, dict):
            for key, value in variables.items():
                if not isinstance(value, str):
                    continue
                if looks_like_env_reference(value):
                    continue
                if (
                    __import__("re").search(
                        r"(?i)(password|secret|token|api[_-]?key)", str(key)
                    )
                    and len(value) >= 6
                ):
                    findings.append(
                        finding(
                            severity="critical",
                            title="Possible hardcoded secret in variables",
                            description=(
                                f"Variable '{key}' looks secret-like and is not an "
                                "environment reference."
                            ),
                            recommendation="Move secrets to masked/protected CI variables.",
                            rule_key="ci_hardcoded_secret",
                        )
                    )
    else:
        findings.extend(scan_sensitive_paths(content))

    return dedupe_findings(findings)
