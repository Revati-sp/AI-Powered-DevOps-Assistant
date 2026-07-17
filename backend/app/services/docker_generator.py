from __future__ import annotations

import json
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_artifact import ArtifactType
from app.models.user import User
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.generators import DockerfileRequest, DockerfileResponse
from app.services.llm.factory import get_llm_provider
from app.services.llm.prompts import DOCKERFILE_SYSTEM_PROMPT


def _deterministic_dockerfile(payload: DockerfileRequest) -> DockerfileResponse:
    language = payload.language.lower()
    if language != "python":
        content = (
            f"# AI-generated placeholder Dockerfile for {payload.language}\n"
            f"# Review and adapt for your stack.\n"
            "FROM alpine:3.20\n"
            "RUN adduser -D appuser\n"
            "USER appuser\n"
            f"EXPOSE {payload.port}\n"
            'CMD ["sleep", "infinity"]\n'
        )
        return DockerfileResponse(
            content=content,
            explanation=[f"Generic template for language '{payload.language}'."],
            warnings=["Non-Python languages use a conservative placeholder template."],
            best_practices=[
                "Pin base image digests in production",
                "Run as non-root",
                "Do not bake secrets into the image",
            ],
            dockerignore_recommendations=[
                ".git",
                ".env",
                "node_modules",
                "__pycache__",
            ],
        )

    python_version = payload.python_version
    user_block = (
        "RUN useradd --create-home --shell /bin/bash appuser\nUSER appuser\n"
        if payload.run_as_non_root
        else ""
    )

    if payload.use_multistage:
        content = f"""# AI-generated Dockerfile — review before production use
FROM python:{python_version}-slim AS builder
WORKDIR /build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \\
    PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:{python_version}-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PATH=/home/appuser/.local/bin:$PATH
COPY --from=builder /install /usr/local
COPY . .
{user_block}EXPOSE {payload.port}
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \\
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:{payload.port}/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{payload.port}"]
"""
    else:
        content = f"""# AI-generated Dockerfile — review before production use
FROM python:{python_version}-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
{user_block}EXPOSE {payload.port}
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{payload.port}"]
"""

    return DockerfileResponse(
        content=content.strip() + "\n",
        explanation=[
            "Uses slim Python base image",
            "Caches dependency installation via requirements.txt copy",
            "Includes health check when multi-stage/runtime image is used",
        ],
        warnings=[]
        if payload.run_as_non_root
        else ["Container may run as root; enable run_as_non_root."],
        best_practices=[
            "Pin dependency versions in requirements.txt",
            "Never copy .env or credentials into the image",
            "Prefer multi-stage builds to reduce final image size",
        ],
        dockerignore_recommendations=[
            ".git",
            ".env",
            ".venv",
            "__pycache__",
            "*.pyc",
            "tests",
            ".pytest_cache",
        ],
    )


class DockerGeneratorService:
    def __init__(self, session: AsyncSession) -> None:
        self.artifacts = ArtifactRepository(session)

    async def generate(
        self, user: User, payload: DockerfileRequest
    ) -> DockerfileResponse:
        base = _deterministic_dockerfile(payload)
        try:
            provider = get_llm_provider(payload.provider)
            prompt = (
                "Improve or validate this Dockerfile generation request. "
                "Return JSON only.\n"
                f"Request: {payload.model_dump_json()}\n"
                f"Baseline:\n{base.content}"
            )
            raw = await provider.generate(
                prompt, system_prompt=DOCKERFILE_SYSTEM_PROMPT
            )
            text = raw.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            result = DockerfileResponse.model_validate(json.loads(text))
        except Exception:  # noqa: BLE001
            result = base

        await self.artifacts.create_artifact(
            user_id=user.id,
            artifact_type=ArtifactType.DOCKERFILE,
            name=f"Dockerfile-{payload.language}",
            content=result.content,
            metadata_json=result.model_dump(exclude={"content"}),
        )
        return result
