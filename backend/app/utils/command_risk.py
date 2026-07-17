from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class RiskAssessment:
    risk_level: RiskLevel
    warnings: list[str]
    requires_confirmation: bool


CRITICAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b"),
        "Recursive force delete",
    ),
    (re.compile(r"\bmkfs(\.|$)"), "Disk formatting"),
    (re.compile(r"\bdd\s+if="), "Raw disk write"),
    (re.compile(r"\bshutdown\b|\breboot\b|\bhalt\b"), "System shutdown/reboot"),
    (
        re.compile(r"\bDROP\s+(TABLE|DATABASE)\b", re.I),
        "Destructive database operation",
    ),
    (re.compile(r"\bterraform\s+destroy\b", re.I), "Terraform destroy"),
    (
        re.compile(r"\bkubectl\s+delete\s+ns(pace)?\b", re.I),
        "Kubernetes namespace deletion",
    ),
    (re.compile(r"\bgit\s+push\s+.*--force\b", re.I), "Force push"),
]

HIGH_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bchmod\s+-R\s+777\b"), "World-writable recursive permissions"),
    (re.compile(r"\bchown\s+-R\b"), "Recursive ownership change"),
    (re.compile(r"\bsudo\s+"), "Elevated privileges"),
    (re.compile(r"\bkubectl\s+delete\b", re.I), "Kubernetes delete operation"),
    (re.compile(r"\bdocker\s+system\s+prune\b", re.I), "Docker prune"),
    (re.compile(r">\s*/dev/sd"), "Writing to block device"),
    (re.compile(r"\bcurl\b.*\|\s*(ba)?sh\b"), "Pipe remote script to shell"),
]

MEDIUM_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\brm\s+"), "File deletion"),
    (re.compile(r"\bkill\b|\bpkill\b"), "Process termination"),
    (re.compile(r"\bsystemctl\s+(stop|restart|disable)\b"), "Service control"),
    (re.compile(r"\biptables\b|\bufw\b"), "Firewall modification"),
]


def classify_command_risk(command: str) -> RiskAssessment:
    warnings: list[str] = []
    level: RiskLevel = "low"

    for pattern, label in CRITICAL_PATTERNS:
        if pattern.search(command):
            warnings.append(f"Critical risk pattern detected: {label}")
            level = "critical"

    if level != "critical":
        for pattern, label in HIGH_PATTERNS:
            if pattern.search(command):
                warnings.append(f"High risk pattern detected: {label}")
                level = "high"

    if level == "low":
        for pattern, label in MEDIUM_PATTERNS:
            if pattern.search(command):
                warnings.append(f"Medium risk pattern detected: {label}")
                level = "medium"

    if level in {"high", "critical"}:
        warnings.append(
            "This command can cause irreversible damage. Confirm intent before running."
        )

    return RiskAssessment(
        risk_level=level,
        warnings=warnings,
        requires_confirmation=level in {"high", "critical"},
    )
