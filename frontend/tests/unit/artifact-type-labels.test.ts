import { describe, expect, it } from "vitest";

import {
  ARTIFACT_TYPE_LABELS,
  ARTIFACT_TYPES,
  artifactTypeLabel,
} from "@/features/artifacts/constants";

describe("artifact type labels", () => {
  it("covers every ArtifactType enum value", () => {
    expect(ARTIFACT_TYPES).toEqual([
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
    ]);

    for (const type of ARTIFACT_TYPES) {
      expect(ARTIFACT_TYPE_LABELS[type]).toBeTruthy();
    }
  });

  it("returns human-readable labels", () => {
    expect(artifactTypeLabel("github-actions")).toBe("GitHub Actions");
    expect(artifactTypeLabel("shell-command")).toBe("Shell command");
    expect(artifactTypeLabel("unknown-type")).toBe("unknown-type");
  });
});
