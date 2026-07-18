from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.test_organizations import _create_org, _register_and_login


@pytest.mark.asyncio
async def test_policy_pack_crud_and_rules(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="policyowner", email="policyowner@example.com"
    )
    org = await _create_org(client, owner_headers, slug="policy-team")

    create_pack = await client.post(
        f"/api/v1/organizations/{org['id']}/policy-packs",
        headers=owner_headers,
        json={
            "name": "Docker Baseline",
            "description": "Baseline docker checks",
            "is_active": True,
        },
    )
    assert create_pack.status_code == 200, create_pack.text
    pack = create_pack.json()["data"]
    pack_id = pack["id"]
    assert pack["name"] == "Docker Baseline"
    assert pack["version"] == 1

    listed = await client.get(
        f"/api/v1/organizations/{org['id']}/policy-packs",
        headers=owner_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    add_rule = await client.post(
        f"/api/v1/organizations/{org['id']}/policy-packs/{pack_id}/rules",
        headers=owner_headers,
        json={
            "rule_key": "require_non_root_container",
            "name": "Non-root container",
            "description": "Containers must not run as root",
            "resource_type": "dockerfile",
            "severity": "high",
            "configuration": {},
            "remediation": "Add USER instruction",
        },
    )
    assert add_rule.status_code == 200, add_rule.text
    rule = add_rule.json()["data"]
    rule_id = rule["id"]

    detail = await client.get(
        f"/api/v1/organizations/{org['id']}/policy-packs/{pack_id}",
        headers=owner_headers,
    )
    assert detail.status_code == 200
    assert len(detail.json()["data"]["rules"]) == 1

    update_rule = await client.patch(
        f"/api/v1/organizations/{org['id']}/policy-packs/{pack_id}/rules/{rule_id}",
        headers=owner_headers,
        json={"severity": "critical", "is_enabled": False},
    )
    assert update_rule.status_code == 200
    assert update_rule.json()["data"]["severity"] == "critical"
    assert update_rule.json()["data"]["is_enabled"] is False

    update_pack = await client.patch(
        f"/api/v1/organizations/{org['id']}/policy-packs/{pack_id}",
        headers=owner_headers,
        json={"name": "Docker Baseline v2", "is_active": True},
    )
    assert update_pack.status_code == 200
    assert update_pack.json()["data"]["name"] == "Docker Baseline v2"
    assert update_pack.json()["data"]["version"] >= 2

    delete_rule = await client.delete(
        f"/api/v1/organizations/{org['id']}/policy-packs/{pack_id}/rules/{rule_id}",
        headers=owner_headers,
    )
    assert delete_rule.status_code == 200

    delete_pack = await client.delete(
        f"/api/v1/organizations/{org['id']}/policy-packs/{pack_id}",
        headers=owner_headers,
    )
    assert delete_pack.status_code == 200

    gone = await client.get(
        f"/api/v1/organizations/{org['id']}/policy-packs/{pack_id}",
        headers=owner_headers,
    )
    assert gone.status_code == 404


@pytest.mark.asyncio
async def test_viewer_cannot_manage_policy_packs(client: AsyncClient) -> None:
    owner_headers = await _register_and_login(
        client, username="polviewowner", email="polviewowner@example.com"
    )
    viewer_headers = await _register_and_login(
        client, username="polviewer", email="polviewer@example.com"
    )
    org = await _create_org(client, owner_headers, slug="policy-viewer-team")

    await client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"email": "polviewer@example.com", "role": "viewer"},
        headers=owner_headers,
    )

    denied = await client.post(
        f"/api/v1/organizations/{org['id']}/policy-packs",
        headers=viewer_headers,
        json={"name": "Blocked Pack", "description": "Should fail"},
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_review_with_organization_policy_packs(
    client: AsyncClient, fake_llm
) -> None:
    owner_headers = await _register_and_login(
        client, username="reviewowner", email="reviewowner@example.com"
    )
    org = await _create_org(client, owner_headers, slug="review-policy-team")

    pack_resp = await client.post(
        f"/api/v1/organizations/{org['id']}/policy-packs",
        headers=owner_headers,
        json={"name": "K8s Pack", "description": "K8s rules", "is_active": True},
    )
    pack_id = pack_resp.json()["data"]["id"]

    await client.post(
        f"/api/v1/organizations/{org['id']}/policy-packs/{pack_id}/rules",
        headers=owner_headers,
        json={
            "rule_key": "forbid_privileged_container",
            "name": "No privileged",
            "description": "Privileged containers are forbidden",
            "resource_type": "kubernetes",
            "severity": "critical",
            "configuration": {},
        },
    )

    fake_llm.response = '{"summary":"Policy review","findings":[]}'

    review = await client.post(
        "/api/v1/review",
        headers=owner_headers,
        json={
            "type": "kubernetes",
            "content": "apiVersion: v1\nkind: Pod\nspec:\n  containers:\n  - privileged: true\n",
            "organization_id": org["id"],
            "policy_pack_ids": [pack_id],
        },
    )
    assert review.status_code == 200, review.text
    data = review.json()["data"]
    assert data["organization_policy_findings"]
    assert any(
        f["source"] == "organization_policy"
        for f in data["organization_policy_findings"]
    )
