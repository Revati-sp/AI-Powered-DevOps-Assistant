import type { components } from "@/lib/api/generated-types";

export type ArtifactType = components["schemas"]["ArtifactType"];

export const ARTIFACT_TYPES: readonly ArtifactType[] = [
  "dockerfile",
  "kubernetes",
  "github-actions",
  "gitlab-ci",
  "jenkins",
  "terraform",
  "shell-command",
  "incident-report",
  "runbook",
  "pipeline",
  "command",
  "review",
  "other",
] as const;

export const ARTIFACT_TYPE_LABELS: Record<ArtifactType, string> = {
  dockerfile: "Dockerfile",
  kubernetes: "Kubernetes",
  "github-actions": "GitHub Actions",
  "gitlab-ci": "GitLab CI",
  jenkins: "Jenkins",
  terraform: "Terraform",
  "shell-command": "Shell command",
  "incident-report": "Incident report",
  runbook: "Runbook",
  pipeline: "Pipeline",
  command: "Command",
  review: "Review",
  other: "Other",
};

export function artifactTypeLabel(type: ArtifactType | string): string {
  if (type in ARTIFACT_TYPE_LABELS) {
    return ARTIFACT_TYPE_LABELS[type as ArtifactType];
  }
  return type;
}
