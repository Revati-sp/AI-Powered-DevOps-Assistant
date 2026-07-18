import { describe, expect, it } from "vitest";

import {
  commandFormSchema,
  dockerfileFormSchema,
  kubernetesFormSchema,
  pipelineFormSchema,
} from "@/features/generators/schemas";

const baseSave = {
  save_artifact: false,
  artifact_name: "",
  artifact_description: "",
  organization_id: null,
  policy_pack_ids: [] as string[],
  validate_policies: false,
};

describe("dockerfileFormSchema", () => {
  it("accepts a valid dockerfile request", () => {
    const result = dockerfileFormSchema.safeParse({
      ...baseSave,
      language: "python",
      framework: "fastapi",
      python_version: "3.12",
      port: 8000,
      use_multistage: true,
      run_as_non_root: true,
      provider: "gemini",
    });
    expect(result.success).toBe(true);
  });

  it("requires artifact name and organization when saving", () => {
    const result = dockerfileFormSchema.safeParse({
      ...baseSave,
      save_artifact: true,
      language: "python",
      framework: "",
      python_version: "3.12",
      port: 8000,
      use_multistage: true,
      run_as_non_root: true,
      provider: "gemini",
    });
    expect(result.success).toBe(false);
  });
});

describe("kubernetesFormSchema", () => {
  it("rejects invalid application names", () => {
    const result = kubernetesFormSchema.safeParse({
      ...baseSave,
      application_name: "Bad_Name",
      image: "nginx:latest",
      replicas: 2,
      container_port: 80,
      service_type: "ClusterIP",
      include_ingress: false,
      include_configmap: true,
      include_hpa: true,
      cpu_request: "100m",
      cpu_limit: "500m",
      memory_request: "128Mi",
      memory_limit: "512Mi",
      provider: "llama",
    });
    expect(result.success).toBe(false);
  });

  it("accepts ClusterIP service type", () => {
    const result = kubernetesFormSchema.safeParse({
      ...baseSave,
      application_name: "my-app",
      image: "nginx:latest",
      replicas: 2,
      container_port: 80,
      service_type: "ClusterIP",
      include_ingress: false,
      include_configmap: true,
      include_hpa: true,
      cpu_request: "100m",
      cpu_limit: "500m",
      memory_request: "128Mi",
      memory_limit: "512Mi",
      provider: "mistral",
    });
    expect(result.success).toBe(true);
  });
});

describe("pipelineFormSchema", () => {
  it("accepts supported platforms and deploy targets", () => {
    const result = pipelineFormSchema.safeParse({
      ...baseSave,
      platform: "github-actions",
      language: "python",
      framework: "fastapi",
      test_command: "pytest",
      build_docker_image: true,
      deploy_target: "none",
      provider: "gemini",
    });
    expect(result.success).toBe(true);
  });
});

describe("commandFormSchema", () => {
  it("requires a request description", () => {
    const result = commandFormSchema.safeParse({
      ...baseSave,
      request: "",
      operating_system: "linux",
      shell: "bash",
      provider: "gemini",
    });
    expect(result.success).toBe(false);
  });

  it("accepts powershell on windows", () => {
    const result = commandFormSchema.safeParse({
      ...baseSave,
      request: "List services",
      operating_system: "windows",
      shell: "powershell",
      provider: "gemini",
    });
    expect(result.success).toBe(true);
  });
});
