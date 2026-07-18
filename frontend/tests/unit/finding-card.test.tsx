import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FindingCard } from "@/components/reviews/finding-card";
import type { ReviewFinding } from "@/features/reviews/types";

const finding: ReviewFinding = {
  severity: "high",
  title: "Root user in container",
  description: "Container runs as root.",
  recommendation: "Set a non-root USER.",
  line: 12,
  source: "static",
  rule_key: "dockerfile.root_user",
};

describe("FindingCard", () => {
  it("renders severity, source label, and recommendation", () => {
    render(<FindingCard finding={finding} />);
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Deterministic (static)")).toBeInTheDocument();
    expect(screen.getByText("Root user in container")).toBeInTheDocument();
    expect(screen.getByText(/Set a non-root USER/)).toBeInTheDocument();
    expect(screen.getByText("Line 12")).toBeInTheDocument();
  });

  it("labels organization policy and llm sources", () => {
    render(
      <FindingCard
        finding={{
          ...finding,
          source: "organization_policy",
          title: "Policy pack rule",
        }}
      />,
    );
    expect(screen.getByText("Organization policy")).toBeInTheDocument();

    render(
      <FindingCard
        finding={{
          ...finding,
          source: "llm",
          title: "AI suggestion",
        }}
      />,
    );
    expect(screen.getByText("AI-assisted (llm)")).toBeInTheDocument();
  });
});
