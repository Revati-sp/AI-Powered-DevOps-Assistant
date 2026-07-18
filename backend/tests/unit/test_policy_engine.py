from __future__ import annotations

import uuid

import pytest
from app.models.policy import PolicyRule
from app.services.policy_engine import evaluate_rule


def _rule(
    rule_key: str,
    *,
    resource_type: str = "general",
    severity: str = "high",
    configuration: dict | None = None,
) -> PolicyRule:
    return PolicyRule(
        id=uuid.uuid4(),
        policy_pack_id=uuid.uuid4(),
        rule_key=rule_key,
        name=rule_key,
        description="test rule",
        resource_type=resource_type,
        severity=severity,
        configuration_json=configuration or {},
        remediation="fix it",
        is_enabled=True,
    )


PACK_ID = uuid.uuid4()


@pytest.mark.parametrize(
    ("rule_key", "resource_type", "content", "configuration"),
    [
        (
            "require_non_root_container",
            "dockerfile",
            "FROM alpine:3.20\nCMD ['sleep','infinity']\n",
            {},
        ),
        (
            "forbid_privileged_container",
            "kubernetes",
            "privileged: true\n",
            {},
        ),
        (
            "forbid_latest_image_tag",
            "kubernetes",
            "image: nginx:latest\n",
            {},
        ),
        (
            "require_resource_limits",
            "kubernetes",
            "kind: Deployment\nspec:\n  template:\n",
            {},
        ),
        (
            "require_liveness_probe",
            "kubernetes",
            "kind: Deployment\nspec:\n  template:\n",
            {},
        ),
        (
            "require_readiness_probe",
            "kubernetes",
            "kind: Deployment\nspec:\n  template:\n",
            {},
        ),
        (
            "require_image_digest",
            "kubernetes",
            "image: nginx:1.2.3\n",
            {},
        ),
        (
            "allowed_container_registries",
            "kubernetes",
            "image: docker.io/library/nginx:1.2.3\n",
            {"registries": ["ghcr.io/company"]},
        ),
        (
            "forbid_host_network",
            "kubernetes",
            "hostNetwork: true\n",
            {},
        ),
        (
            "forbid_host_path",
            "kubernetes",
            "volumes:\n- hostPath:\n    path: /etc\n",
            {},
        ),
        (
            "required_kubernetes_labels",
            "kubernetes",
            "metadata:\n  labels:\n    app: demo\n",
            {"labels": ["app.kubernetes.io/name"]},
        ),
        (
            "forbid_github_write_all",
            "github-actions",
            "permissions: write-all\n",
            {},
        ),
        (
            "require_pinned_github_actions",
            "github-actions",
            "jobs:\n  build:\n    steps:\n      - uses: actions/checkout@v3\n",
            {},
        ),
        (
            "require_terraform_encryption",
            "terraform",
            'resource "aws_s3_bucket" "b" {}\n',
            {},
        ),
        (
            "forbid_public_cloud_storage",
            "terraform",
            'acl = "public-read"\n',
            {},
        ),
    ],
)
def test_policy_rules_flag_violations(
    rule_key: str,
    resource_type: str,
    content: str,
    configuration: dict,
) -> None:
    rule = _rule(rule_key, resource_type=resource_type, configuration=configuration)
    findings = evaluate_rule(
        rule,
        config_type=resource_type,
        content=content,
        policy_pack_id=PACK_ID,
    )
    assert findings, f"Expected finding for {rule_key}"


def test_require_non_root_container_passes_with_user() -> None:
    rule = _rule("require_non_root_container", resource_type="dockerfile")
    findings = evaluate_rule(
        rule,
        config_type="dockerfile",
        content="FROM alpine\nUSER app\n",
        policy_pack_id=PACK_ID,
    )
    assert findings == []
