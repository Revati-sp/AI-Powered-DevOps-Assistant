import { describe, expect, it } from "vitest";

import { reviewFormSchema } from "@/features/reviews/schemas";
import { FINDING_SOURCE_LABELS } from "@/features/reviews/types";

describe("reviewFormSchema", () => {
  it("accepts supported review types", () => {
    for (const type of ["dockerfile", "kubernetes", "terraform", "github-actions"] as const) {
      const result = reviewFormSchema.safeParse({
        type,
        content: "FROM python:3.12",
        provider: "gemini",
        organization_id: null,
        policy_pack_ids: [],
      });
      expect(result.success).toBe(true);
    }
  });

  it("rejects empty content", () => {
    const result = reviewFormSchema.safeParse({
      type: "dockerfile",
      content: "",
      provider: "gemini",
      organization_id: null,
      policy_pack_ids: [],
    });
    expect(result.success).toBe(false);
  });
});

describe("FINDING_SOURCE_LABELS", () => {
  it("labels static, organization policy, and llm sources", () => {
    expect(FINDING_SOURCE_LABELS.static).toBe("Deterministic (static)");
    expect(FINDING_SOURCE_LABELS.organization_policy).toBe("Organization policy");
    expect(FINDING_SOURCE_LABELS.llm).toBe("AI-assisted (llm)");
  });
});
