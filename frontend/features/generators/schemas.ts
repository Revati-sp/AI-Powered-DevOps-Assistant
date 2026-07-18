import { z } from "zod";

import { LLM_PROVIDERS } from "@/lib/constants/app";

export const providerSchema = z.enum(LLM_PROVIDERS);

const saveOptionsFields = {
  save_artifact: z.boolean(),
  artifact_name: z.string().trim().max(200),
  artifact_description: z.string().trim().max(2000),
  organization_id: z.string().uuid().nullable().optional(),
  policy_pack_ids: z.array(z.string().uuid()),
  validate_policies: z.boolean(),
};

function refineSaveOptions(
  value: {
    save_artifact: boolean;
    artifact_name: string;
    organization_id?: string | null;
    validate_policies: boolean;
  },
  ctx: z.RefinementCtx,
) {
  if (value.save_artifact) {
    if (!value.artifact_name.trim()) {
      ctx.addIssue({
        code: "custom",
        path: ["artifact_name"],
        message: "Artifact name is required when saving",
      });
    }
    if (!value.organization_id) {
      ctx.addIssue({
        code: "custom",
        path: ["organization_id"],
        message: "Select an organization to save an artifact",
      });
    }
  }
  if (value.validate_policies && !value.organization_id) {
    ctx.addIssue({
      code: "custom",
      path: ["validate_policies"],
      message: "Select an organization to validate policies",
    });
  }
}

export const saveOptionsSchema = z.object(saveOptionsFields).superRefine(refineSaveOptions);

export type SaveOptionsValues = z.infer<typeof saveOptionsSchema>;

export const dockerfileFormSchema = z
  .object({
    ...saveOptionsFields,
    language: z.string().trim().min(1, "Language is required").max(100),
    framework: z.string().trim().max(100),
    python_version: z.string().trim().min(1),
    port: z.number().int().min(1).max(65535),
    use_multistage: z.boolean(),
    run_as_non_root: z.boolean(),
    provider: providerSchema,
  })
  .superRefine(refineSaveOptions);

export type DockerfileFormValues = z.infer<typeof dockerfileFormSchema>;

export const kubernetesFormSchema = z
  .object({
    ...saveOptionsFields,
    application_name: z
      .string()
      .trim()
      .min(1, "Application name is required")
      .max(100)
      .regex(
        /^[a-z0-9]([-a-z0-9]*[a-z0-9])?$/,
        "Use a valid DNS label (lowercase alphanumeric and hyphens)",
      ),
    image: z.string().trim().min(1, "Image is required").max(500),
    replicas: z.number().int().min(1).max(100),
    container_port: z.number().int().min(1).max(65535),
    service_type: z.enum(["ClusterIP", "NodePort", "LoadBalancer"]),
    include_ingress: z.boolean(),
    include_configmap: z.boolean(),
    include_hpa: z.boolean(),
    cpu_request: z.string().trim().min(1),
    cpu_limit: z.string().trim().min(1),
    memory_request: z.string().trim().min(1),
    memory_limit: z.string().trim().min(1),
    provider: providerSchema,
  })
  .superRefine(refineSaveOptions);

export type KubernetesFormValues = z.infer<typeof kubernetesFormSchema>;

export const pipelineFormSchema = z
  .object({
    ...saveOptionsFields,
    platform: z.enum(["github-actions", "gitlab-ci", "jenkins"]),
    language: z.string().trim().min(1),
    framework: z.string().trim().max(100),
    test_command: z.string().trim().min(1),
    build_docker_image: z.boolean(),
    deploy_target: z.enum(["none", "kubernetes", "docker-host"]),
    provider: providerSchema,
  })
  .superRefine(refineSaveOptions);

export type PipelineFormValues = z.infer<typeof pipelineFormSchema>;

export const commandFormSchema = z
  .object({
    ...saveOptionsFields,
    request: z.string().trim().min(1, "Describe the command you need").max(4000),
    operating_system: z.enum(["linux", "macos", "windows"]),
    shell: z.enum(["bash", "zsh", "sh", "powershell"]),
    provider: providerSchema,
  })
  .superRefine(refineSaveOptions);

export type CommandFormValues = z.infer<typeof commandFormSchema>;

export const defaultSaveOptions = {
  save_artifact: false,
  artifact_name: "",
  artifact_description: "",
  organization_id: null as string | null,
  policy_pack_ids: [] as string[],
  validate_policies: false,
};

export function toSavePayload(values: SaveOptionsValues) {
  return {
    save_artifact: values.save_artifact,
    artifact_name: values.save_artifact ? values.artifact_name.trim() || null : null,
    artifact_description: values.save_artifact ? values.artifact_description.trim() || null : null,
    organization_id: values.organization_id ?? null,
    policy_pack_ids: values.policy_pack_ids ?? [],
    validate_policies: values.validate_policies,
  };
}
