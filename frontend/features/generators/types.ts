import type { components } from "@/lib/api/generated-types";

export type DockerfileRequest = components["schemas"]["DockerfileRequest"];
export type DockerfileResponse = components["schemas"]["DockerfileResponse"];
export type KubernetesRequest = components["schemas"]["KubernetesRequest"];
export type KubernetesResponse = components["schemas"]["KubernetesResponse"];
export type PipelineRequest = components["schemas"]["PipelineRequest"];
export type PipelineResponse = components["schemas"]["PipelineResponse"];
export type ShellCommandRequest = components["schemas"]["ShellCommandRequest"];
export type ShellCommandResponse = components["schemas"]["ShellCommandResponse"];
export type PolicyFinding = components["schemas"]["PolicyFinding"];

export type GeneratorKind = "dockerfile" | "kubernetes" | "pipeline" | "command";

export type GeneratorOutputBase = {
  content: string;
  disclaimer: string;
  explanation?: string[];
  warnings?: string[];
  best_practices?: string[];
  policy_findings?: PolicyFinding[];
  saved_artifact_id?: string | null;
  filename?: string;
  /** Command-only fields */
  command?: string;
  risk_level?: ShellCommandResponse["risk_level"];
  requires_confirmation?: boolean;
};
