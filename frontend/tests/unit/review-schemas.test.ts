import { describe, expect, it } from "vitest";

import { reviewFormSchema, reviewTypeSchema } from "@/features/reviews/schemas";
import {
  FINDING_SOURCE_LABELS,
  REVIEW_TYPE_HINTS,
  REVIEW_TYPE_LABELS,
  REVIEW_TYPE_SAMPLES,
} from "@/features/reviews/types";

describe("reviewFormSchema", () => {
  it("accepts all supported review types including gitlab-ci and jenkins", () => {
    for (const type of reviewTypeSchema.options) {
      const result = reviewFormSchema.safeParse({
        type,
        content: REVIEW_TYPE_SAMPLES[type],
        provider: "gemini",
        organization_id: null,
        policy_pack_ids: [],
      });
      expect(result.success).toBe(true);
    }
  });

  it("rejects unknown review types", () => {
    const result = reviewFormSchema.safeParse({
      type: "circleci",
      content: "jobs: {}",
      provider: "gemini",
      organization_id: null,
      policy_pack_ids: [],
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty content", () => {
    const result = reviewFormSchema.safeParse({
      type: "gitlab-ci",
      content: "",
      provider: "gemini",
      organization_id: null,
      policy_pack_ids: [],
    });
    expect(result.success).toBe(false);
  });
});

describe("review type presentation", () => {
  it("labels and hints cover gitlab-ci and jenkins", () => {
    expect(REVIEW_TYPE_LABELS["gitlab-ci"]).toBe("GitLab CI");
    expect(REVIEW_TYPE_LABELS.jenkins).toBe("Jenkins");
    expect(REVIEW_TYPE_HINTS["gitlab-ci"]).toMatch(/gitlab-ci/i);
    expect(REVIEW_TYPE_HINTS.jenkins).toMatch(/Jenkinsfile/i);
  });

  it("labels static, organization policy, and llm sources", () => {
    expect(FINDING_SOURCE_LABELS.static).toBe("Deterministic (static)");
    expect(FINDING_SOURCE_LABELS.organization_policy).toBe("Organization policy");
    expect(FINDING_SOURCE_LABELS.llm).toBe("AI-assisted (llm)");
  });
});
