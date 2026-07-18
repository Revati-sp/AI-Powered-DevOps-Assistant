import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";

import type {
  DockerfileRequest,
  DockerfileResponse,
  KubernetesRequest,
  KubernetesResponse,
  PipelineRequest,
  PipelineResponse,
  ShellCommandRequest,
  ShellCommandResponse,
} from "@/features/generators/types";

export function generateDockerfile(body: DockerfileRequest) {
  return apiFetch<DockerfileResponse>(endpoints.generate.dockerfile(), {
    method: "POST",
    body,
    timeoutMs: 120_000,
  });
}

export function generateKubernetes(body: KubernetesRequest) {
  return apiFetch<KubernetesResponse>(endpoints.generate.kubernetes(), {
    method: "POST",
    body,
    timeoutMs: 120_000,
  });
}

export function generatePipeline(body: PipelineRequest) {
  return apiFetch<PipelineResponse>(endpoints.generate.pipeline(), {
    method: "POST",
    body,
    timeoutMs: 120_000,
  });
}

export function generateCommand(body: ShellCommandRequest) {
  return apiFetch<ShellCommandResponse>(endpoints.generate.command(), {
    method: "POST",
    body,
    timeoutMs: 120_000,
  });
}
