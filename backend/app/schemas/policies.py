from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

PolicySeverity = Literal["low", "medium", "high", "critical"]
PolicyResourceType = Literal[
    "dockerfile",
    "kubernetes",
    "terraform",
    "github-actions",
    "gitlab-ci",
    "jenkins",
    "general",
]

SUPPORTED_RULE_KEYS = frozenset(
    {
        "require_non_root_container",
        "forbid_privileged_container",
        "forbid_latest_image_tag",
        "require_resource_limits",
        "require_liveness_probe",
        "require_readiness_probe",
        "require_image_digest",
        "allowed_container_registries",
        "forbid_host_network",
        "forbid_host_path",
        "required_kubernetes_labels",
        "forbid_github_write_all",
        "require_pinned_github_actions",
        "require_terraform_encryption",
        "forbid_public_cloud_storage",
    }
)


class EmptyRuleConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AllowedRegistriesConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    registries: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_registries(self) -> AllowedRegistriesConfiguration:
        cleaned = [item.strip() for item in self.registries if item.strip()]
        if not cleaned:
            raise ValueError("registries must not be empty")
        self.registries = cleaned
        return self


class RequiredLabelsConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    labels: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_labels(self) -> RequiredLabelsConfiguration:
        cleaned = [item.strip() for item in self.labels if item.strip()]
        if not cleaned:
            raise ValueError("labels must not be empty")
        self.labels = cleaned
        return self


RULE_CONFIGURATION_MODELS: dict[str, type[BaseModel]] = {
    "require_non_root_container": EmptyRuleConfiguration,
    "forbid_privileged_container": EmptyRuleConfiguration,
    "forbid_latest_image_tag": EmptyRuleConfiguration,
    "require_resource_limits": EmptyRuleConfiguration,
    "require_liveness_probe": EmptyRuleConfiguration,
    "require_readiness_probe": EmptyRuleConfiguration,
    "require_image_digest": EmptyRuleConfiguration,
    "forbid_host_network": EmptyRuleConfiguration,
    "forbid_host_path": EmptyRuleConfiguration,
    "forbid_github_write_all": EmptyRuleConfiguration,
    "require_pinned_github_actions": EmptyRuleConfiguration,
    "require_terraform_encryption": EmptyRuleConfiguration,
    "forbid_public_cloud_storage": EmptyRuleConfiguration,
    "allowed_container_registries": AllowedRegistriesConfiguration,
    "required_kubernetes_labels": RequiredLabelsConfiguration,
}


def validate_rule_configuration(
    rule_key: str, configuration: dict[str, Any]
) -> dict[str, Any]:
    if rule_key not in SUPPORTED_RULE_KEYS:
        raise ValueError(f"Unsupported rule_key: {rule_key}")
    model = RULE_CONFIGURATION_MODELS[rule_key]
    return model.model_validate(configuration or {}).model_dump()


class PolicyFinding(BaseModel):
    rule_key: str
    severity: PolicySeverity
    title: str
    description: str
    recommendation: str
    source: Literal["organization_policy"] = "organization_policy"
    policy_pack_id: UUID
    line: int | None = None


class PolicyRuleCreateRequest(BaseModel):
    rule_key: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    resource_type: PolicyResourceType
    severity: PolicySeverity
    configuration: dict[str, Any] = Field(default_factory=dict)
    remediation: str | None = None
    is_enabled: bool = True

    @model_validator(mode="after")
    def validate_configuration(self) -> PolicyRuleCreateRequest:
        validate_rule_configuration(self.rule_key, self.configuration)
        return self


class PolicyRuleUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    severity: PolicySeverity | None = None
    configuration: dict[str, Any] | None = None
    remediation: str | None = None
    is_enabled: bool | None = None


class PolicyRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    policy_pack_id: UUID
    rule_key: str
    name: str
    description: str
    resource_type: str
    severity: str
    configuration_json: dict[str, Any]
    remediation: str | None
    is_enabled: bool


class PolicyPackCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    is_active: bool = True


class PolicyPackUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    is_active: bool | None = None


class PolicyPackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    is_active: bool
    version: int
    created_by: UUID


class PolicyPackDetailResponse(PolicyPackResponse):
    rules: list[PolicyRuleResponse] = Field(default_factory=list)
