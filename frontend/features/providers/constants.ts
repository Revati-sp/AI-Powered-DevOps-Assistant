import type { LLMOperation } from "./types";

export const OPERATION_LABELS: Record<LLMOperation, string> = {
  chat: "Chat",
  log_analysis: "Log analysis",
  configuration_review: "Configuration review",
  dockerfile_generation: "Dockerfile generation",
  kubernetes: "Kubernetes generation",
};

export function operationLabel(operation: string): string {
  return OPERATION_LABELS[operation as LLMOperation] ?? operation.replace(/_/g, " ");
}
