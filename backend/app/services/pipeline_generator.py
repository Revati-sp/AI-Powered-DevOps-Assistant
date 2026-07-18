from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_artifact import ArtifactType
from app.models.user import User
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.generators import PipelineRequest, PipelineResponse
from app.services.audit_service import AuditRequestContext
from app.services.generator_artifact_helper import apply_generator_policies_and_save


def _github_actions(payload: PipelineRequest) -> tuple[str, str]:
    deploy = ""
    if payload.build_docker_image:
        deploy += """
      - name: Build Docker image
        run: docker build -t ${{ secrets.REGISTRY_IMAGE }}:${{ github.sha }} .
      - name: Push Docker image
        run: |
          echo "Use registry credentials from CI secrets"
          # docker push ${{ secrets.REGISTRY_IMAGE }}:${{ github.sha }}
"""
    if payload.deploy_target == "kubernetes":
        deploy += """
      - name: Deploy to Kubernetes (placeholder)
        run: |
          echo "Apply manifests with kubeconfig from secrets — not executed here"
          # kubectl apply -f k8s/
"""

    content = f"""# AI-generated GitHub Actions workflow — review before use
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Lint
        run: ruff check .
      - name: Unit tests
        run: {payload.test_command}
      - name: Security checks
        run: |
          pip install pip-audit
          pip-audit || true
{deploy}
"""
    return content.strip() + "\n", ".github/workflows/ci.yml"


def _gitlab_ci(payload: PipelineRequest) -> tuple[str, str]:
    content = f"""# AI-generated GitLab CI — review before use
stages:
  - lint
  - test
  - build
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

lint:
  stage: lint
  image: python:3.12-slim
  script:
    - pip install ruff
    - ruff check .

test:
  stage: test
  image: python:3.12-slim
  script:
    - pip install -r requirements.txt
    - {payload.test_command}

build:
  stage: build
  image: docker:27
  services:
    - docker:27-dind
  script:
    - echo "Build and push using CI_REGISTRY_* variables from GitLab"
    - docker build -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA" .
    # - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA"
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: {"on_success" if payload.build_docker_image else "never"}

deploy:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - echo "Deploy placeholder — provide KUBECONFIG via CI variables"
    # - kubectl apply -f k8s/
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: {"on_success" if payload.deploy_target != "none" else "never"}
"""
    return content.strip() + "\n", ".gitlab-ci.yml"


def _jenkins(payload: PipelineRequest) -> tuple[str, str]:
    content = f"""// AI-generated Jenkinsfile — review before use
pipeline {{
  agent any
  options {{
    timestamps()
    disableConcurrentBuilds()
  }}
  environment {{
    // Credentials must come from Jenkins credentials store
    REGISTRY_CREDS = credentials('registry-credentials')
  }}
  stages {{
    stage('Install') {{
      steps {{
        sh 'python -m pip install -r requirements.txt'
      }}
    }}
    stage('Lint') {{
      steps {{
        sh 'ruff check .'
      }}
    }}
    stage('Test') {{
      steps {{
        sh '{payload.test_command}'
      }}
    }}
    stage('Security') {{
      steps {{
        sh 'pip install pip-audit && pip-audit || true'
      }}
    }}
    stage('Docker') {{
      when {{ expression {{ return {str(payload.build_docker_image).lower()} }} }}
      steps {{
        sh 'docker build -t $REGISTRY_IMAGE:$GIT_COMMIT .'
        // sh 'docker push $REGISTRY_IMAGE:$GIT_COMMIT'
      }}
    }}
    stage('Deploy') {{
      when {{ expression {{ return {"true" if payload.deploy_target != "none" else "false"} }} }}
      steps {{
        echo 'Deploy placeholder — not executed by this assistant'
      }}
    }}
  }}
}}
"""
    return content.strip() + "\n", "Jenkinsfile"


class PipelineGeneratorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.artifacts = ArtifactRepository(session)

    async def generate(
        self,
        user: User,
        payload: PipelineRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> PipelineResponse:
        if payload.platform == "github-actions":
            content, filename = _github_actions(payload)
        elif payload.platform == "gitlab-ci":
            content, filename = _gitlab_ci(payload)
        else:
            content, filename = _jenkins(payload)

        result = PipelineResponse(
            content=content,
            filename=filename,
            explanation=[
                "Includes install, lint, test, and security stages",
                "Docker/deploy steps are placeholders that use CI secret stores",
            ],
            warnings=[
                "Never commit credentials into pipeline files",
                "Review workflow permissions before enabling deployments",
            ],
            best_practices=[
                "Pin action/image versions",
                "Use least-privilege CI permissions",
                "Require manual approval for production deploys",
            ],
        )

        policy_findings, saved_artifact_id = await apply_generator_policies_and_save(
            self.session,
            user,
            payload,
            artifact_type=ArtifactType.PIPELINE,
            content=result.content,
            default_name=filename,
            metadata=result.model_dump(
                exclude={"content", "policy_findings", "saved_artifact_id"}
            ),
            audit_context=audit_context,
        )
        result.policy_findings = policy_findings
        result.saved_artifact_id = saved_artifact_id

        if not payload.save_artifact:
            await self.artifacts.create_artifact(
                user_id=user.id,
                artifact_type=ArtifactType.PIPELINE,
                name=filename,
                content=result.content,
                metadata_json=result.model_dump(
                    exclude={"content", "policy_findings", "saved_artifact_id"}
                ),
            )
        return result
