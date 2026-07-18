from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.policies import PolicyFinding


class GeneratorSaveOptions(BaseModel):
    save_artifact: bool = False
    artifact_name: str | None = None
    artifact_description: str | None = None
    organization_id: UUID | None = None
    policy_pack_ids: list[UUID] = Field(default_factory=list)
    validate_policies: bool = False


class DockerfileRequest(GeneratorSaveOptions):
    language: str = Field(min_length=1, max_length=50)
    framework: str | None = None
    python_version: str = "3.12"
    port: int = Field(default=8000, ge=1, le=65535)
    use_multistage: bool = True
    run_as_non_root: bool = True
    provider: str = "gemini"


class DockerfileResponse(BaseModel):
    content: str
    explanation: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    best_practices: list[str] = Field(default_factory=list)
    dockerignore_recommendations: list[str] = Field(default_factory=list)
    policy_findings: list[PolicyFinding] = Field(default_factory=list)
    saved_artifact_id: UUID | None = None
    disclaimer: str = (
        "AI-generated Dockerfile. Review carefully before use in production."
    )


class KubernetesRequest(GeneratorSaveOptions):
    application_name: str = Field(
        min_length=1, max_length=63, pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"
    )
    image: str = Field(min_length=1, max_length=255)
    replicas: int = Field(default=2, ge=1, le=100)
    container_port: int = Field(default=8000, ge=1, le=65535)
    service_type: Literal["ClusterIP", "NodePort", "LoadBalancer"] = "ClusterIP"
    include_ingress: bool = False
    include_configmap: bool = True
    include_hpa: bool = True
    cpu_request: str = "100m"
    cpu_limit: str = "500m"
    memory_request: str = "128Mi"
    memory_limit: str = "512Mi"
    provider: str = "gemini"


class KubernetesResponse(BaseModel):
    content: str
    explanation: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    best_practices: list[str] = Field(default_factory=list)
    policy_findings: list[PolicyFinding] = Field(default_factory=list)
    saved_artifact_id: UUID | None = None
    disclaimer: str = (
        "AI-generated Kubernetes manifests. Validate and review before apply."
    )


class PipelineRequest(GeneratorSaveOptions):
    platform: Literal["github-actions", "gitlab-ci", "jenkins"]
    language: str = "python"
    framework: str | None = "fastapi"
    test_command: str = "pytest"
    build_docker_image: bool = True
    deploy_target: Literal["none", "kubernetes", "docker-host"] = "kubernetes"
    provider: str = "gemini"


class PipelineResponse(BaseModel):
    content: str
    filename: str
    explanation: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    best_practices: list[str] = Field(default_factory=list)
    policy_findings: list[PolicyFinding] = Field(default_factory=list)
    saved_artifact_id: UUID | None = None
    disclaimer: str = (
        "AI-generated CI/CD pipeline. Secrets must come from your CI secret store."
    )


class ShellCommandRequest(GeneratorSaveOptions):
    request: str = Field(min_length=1, max_length=2000)
    operating_system: Literal["linux", "macos", "windows"] = "linux"
    shell: Literal["bash", "zsh", "sh", "powershell"] = "bash"
    provider: str = "gemini"


class ShellCommandResponse(BaseModel):
    command: str
    explanation: str
    risk_level: Literal["low", "medium", "high", "critical"]
    warnings: list[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    policy_findings: list[PolicyFinding] = Field(default_factory=list)
    saved_artifact_id: UUID | None = None
    disclaimer: str = "Suggested command only. It was not executed by this assistant."
