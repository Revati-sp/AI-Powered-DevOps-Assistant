export const SUPPORTED_RULE_KEYS = [
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
] as const;

export type SupportedRuleKey = (typeof SUPPORTED_RULE_KEYS)[number];

export const RULE_KEYS_WITH_LIST_CONFIG = [
  "allowed_container_registries",
  "required_kubernetes_labels",
] as const;

export type ListConfigRuleKey = (typeof RULE_KEYS_WITH_LIST_CONFIG)[number];

export function isListConfigRuleKey(ruleKey: string): ruleKey is ListConfigRuleKey {
  return (RULE_KEYS_WITH_LIST_CONFIG as readonly string[]).includes(ruleKey);
}

export function listConfigFieldName(ruleKey: ListConfigRuleKey): "registries" | "labels" {
  return ruleKey === "allowed_container_registries" ? "registries" : "labels";
}

export const RULE_KEY_LABELS: Record<SupportedRuleKey, string> = {
  require_non_root_container: "Require non-root container",
  forbid_privileged_container: "Forbid privileged container",
  forbid_latest_image_tag: "Forbid latest image tag",
  require_resource_limits: "Require resource limits",
  require_liveness_probe: "Require liveness probe",
  require_readiness_probe: "Require readiness probe",
  require_image_digest: "Require image digest",
  allowed_container_registries: "Allowed container registries",
  forbid_host_network: "Forbid host network",
  forbid_host_path: "Forbid host path",
  required_kubernetes_labels: "Required Kubernetes labels",
  forbid_github_write_all: "Forbid GitHub write-all",
  require_pinned_github_actions: "Require pinned GitHub Actions",
  require_terraform_encryption: "Require Terraform encryption",
  forbid_public_cloud_storage: "Forbid public cloud storage",
};

export const POLICY_RESOURCE_TYPES = [
  "dockerfile",
  "kubernetes",
  "terraform",
  "github-actions",
  "gitlab-ci",
  "jenkins",
  "general",
] as const;

export type PolicyResourceType = (typeof POLICY_RESOURCE_TYPES)[number];

export const POLICY_SEVERITIES = ["low", "medium", "high", "critical"] as const;

export type PolicySeverity = (typeof POLICY_SEVERITIES)[number];
