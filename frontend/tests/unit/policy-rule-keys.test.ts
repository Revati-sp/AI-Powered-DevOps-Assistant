import { describe, expect, it } from "vitest";

import {
  isListConfigRuleKey,
  listConfigFieldName,
  SUPPORTED_RULE_KEYS,
} from "@/features/policies/constants";

describe("SUPPORTED_RULE_KEYS", () => {
  it("includes the backend-supported rule keys", () => {
    expect(SUPPORTED_RULE_KEYS).toEqual([
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
    ]);
  });

  it("identifies list-config rules and their fields", () => {
    expect(isListConfigRuleKey("allowed_container_registries")).toBe(true);
    expect(isListConfigRuleKey("required_kubernetes_labels")).toBe(true);
    expect(isListConfigRuleKey("forbid_host_path")).toBe(false);
    expect(listConfigFieldName("allowed_container_registries")).toBe("registries");
    expect(listConfigFieldName("required_kubernetes_labels")).toBe("labels");
  });
});
