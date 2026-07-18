from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_review_accepts_gitlab_ci_and_jenkins(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    gitlab = await client.post(
        "/api/v1/review",
        headers=auth_headers,
        json={
            "type": "gitlab-ci",
            "content": "test:\n  image: python:3.12-slim\n  script:\n    - pytest\n",
            "provider": "gemini",
        },
    )
    assert gitlab.status_code == 200, gitlab.text
    body = gitlab.json()["data"]
    assert "score" in body
    assert "findings" in body

    jenkins = await client.post(
        "/api/v1/review",
        headers=auth_headers,
        json={
            "type": "jenkins",
            "content": (
                "pipeline {\n  agent any\n  options { timeout(time: 10, unit: 'MINUTES') }\n"
                "  post { always { echo 'done' } }\n"
                "  stages { stage('T') { steps { sh 'true' } } } }\n}"
            ),
            "provider": "gemini",
        },
    )
    assert jenkins.status_code == 200, jenkins.text


@pytest.mark.asyncio
async def test_review_rejects_unknown_type(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/review",
        headers=auth_headers,
        json={
            "type": "circleci",
            "content": "jobs: {}\n",
            "provider": "gemini",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_review_oversized_content_rejected(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/review",
        headers=auth_headers,
        json={
            "type": "gitlab-ci",
            "content": "x" * 500_001,
            "provider": "gemini",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_existing_dockerfile_review_still_works(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/review",
        headers=auth_headers,
        json={
            "type": "dockerfile",
            "content": "FROM alpine:3.20\nUSER nobody\n",
            "provider": "gemini",
        },
    )
    assert response.status_code == 200, response.text
