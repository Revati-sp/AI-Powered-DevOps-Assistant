import type { components } from "@/lib/api/generated-types";

export type ReviewRequest = components["schemas"]["ReviewRequest"];
export type ReviewResponse = components["schemas"]["ReviewResponse"];
export type ReviewFinding = components["schemas"]["ReviewFinding"];
export type ReviewType = ReviewRequest["type"];
export type FindingSource = ReviewFinding["source"];
export type FindingSeverity = ReviewFinding["severity"];

export const FINDING_SOURCE_LABELS: Record<FindingSource, string> = {
  static: "Deterministic (static)",
  organization_policy: "Organization policy",
  llm: "AI-assisted (llm)",
};
