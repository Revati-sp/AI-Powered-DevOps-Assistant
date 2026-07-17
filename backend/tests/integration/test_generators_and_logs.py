import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_log_analysis_and_file_size_rejection(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "1")
    from app.core.config import get_settings

    get_settings.cache_clear()

    analyze = await client.post(
        "/api/v1/logs/analyze",
        headers=auth_headers,
        json={
            "content": "Pod foo CrashLoopBackOff\nERROR: Job failed\n",
            "provider": "gemini",
        },
    )
    assert analyze.status_code == 200
    data = analyze.json()["data"]
    assert "summary" in data
    assert data["severity"] in {"low", "medium", "high", "critical"}

    # Restore settings and reject oversized uploads via validation helper path.
    get_settings.cache_clear()
    big = io.BytesIO(b"x" * (6 * 1024 * 1024))
    upload = await client.post(
        "/api/v1/logs/analyze/upload",
        headers=auth_headers,
        files={"file": ("huge.log", big, "text/plain")},
        data={"provider": "gemini"},
    )
    assert upload.status_code == 422


@pytest.mark.asyncio
async def test_dockerfile_kubernetes_pipeline_command(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    dockerfile = await client.post(
        "/api/v1/generate/dockerfile",
        headers=auth_headers,
        json={
            "language": "python",
            "framework": "fastapi",
            "python_version": "3.12",
            "port": 8000,
            "use_multistage": True,
            "run_as_non_root": True,
        },
    )
    assert dockerfile.status_code == 200
    assert "FROM python" in dockerfile.json()["data"]["content"]

    k8s = await client.post(
        "/api/v1/generate/kubernetes",
        headers=auth_headers,
        json={
            "application_name": "payment-api",
            "image": "payment-api:latest",
            "replicas": 3,
            "container_port": 8000,
            "service_type": "ClusterIP",
            "include_ingress": False,
            "include_configmap": True,
            "include_hpa": True,
        },
    )
    assert k8s.status_code == 200
    body = k8s.json()["data"]
    assert "kind: Deployment" in body["content"]
    assert any("latest" in w.lower() for w in body["warnings"])

    pipeline = await client.post(
        "/api/v1/generate/pipeline",
        headers=auth_headers,
        json={
            "platform": "github-actions",
            "language": "python",
            "framework": "fastapi",
            "test_command": "pytest",
            "build_docker_image": True,
            "deploy_target": "kubernetes",
        },
    )
    assert pipeline.status_code == 200
    assert "jobs:" in pipeline.json()["data"]["content"]

    command = await client.post(
        "/api/v1/generate/command",
        headers=auth_headers,
        json={
            "request": "Find files larger than 1 GB in /var",
            "operating_system": "linux",
            "shell": "bash",
        },
    )
    assert command.status_code == 200
    assert "find" in command.json()["data"]["command"]


@pytest.mark.asyncio
async def test_review_endpoint(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/review",
        headers=auth_headers,
        json={
            "type": "dockerfile",
            "content": 'FROM python:3.12\nCMD ["python", "app.py"]\n',
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data["score"], int)
    assert data["findings"]
