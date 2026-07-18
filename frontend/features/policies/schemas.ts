import { z } from "zod";

import { POLICY_RESOURCE_TYPES, POLICY_SEVERITIES, SUPPORTED_RULE_KEYS } from "./constants";

export const policyPackFormSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(200),
  description: z.string().trim().max(2000).optional().or(z.literal("")),
  is_active: z.boolean(),
});

export type PolicyPackFormValues = z.infer<typeof policyPackFormSchema>;

export const policyRuleFormSchema = z
  .object({
    rule_key: z.enum(SUPPORTED_RULE_KEYS),
    name: z.string().trim().min(1, "Name is required").max(200),
    description: z.string().trim().min(1, "Description is required"),
    resource_type: z.enum(POLICY_RESOURCE_TYPES),
    severity: z.enum(POLICY_SEVERITIES),
    remediation: z.string().trim().optional().or(z.literal("")),
    is_enabled: z.boolean(),
    list_items: z.string().optional(),
  })
  .superRefine((values, ctx) => {
    if (
      values.rule_key === "allowed_container_registries" ||
      values.rule_key === "required_kubernetes_labels"
    ) {
      const items = (values.list_items ?? "")
        .split(/[\n,]/)
        .map((item) => item.trim())
        .filter(Boolean);
      if (items.length === 0) {
        ctx.addIssue({
          code: "custom",
          path: ["list_items"],
          message:
            values.rule_key === "allowed_container_registries"
              ? "Add at least one registry"
              : "Add at least one label",
        });
      }
    }
  });

export type PolicyRuleFormValues = z.infer<typeof policyRuleFormSchema>;

export function configurationFromRuleForm(values: PolicyRuleFormValues): Record<string, unknown> {
  if (values.rule_key === "allowed_container_registries") {
    return {
      registries: (values.list_items ?? "")
        .split(/[\n,]/)
        .map((item) => item.trim())
        .filter(Boolean),
    };
  }
  if (values.rule_key === "required_kubernetes_labels") {
    return {
      labels: (values.list_items ?? "")
        .split(/[\n,]/)
        .map((item) => item.trim())
        .filter(Boolean),
    };
  }
  return {};
}
