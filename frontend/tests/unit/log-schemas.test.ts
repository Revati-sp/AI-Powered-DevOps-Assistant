import { describe, expect, it } from "vitest";

import {
  LOG_CONTENT_MAX,
  logAnalyzePasteSchema,
  logAnalyzeResultSchema,
} from "@/features/logs/schemas";
import { taskPollInterval } from "@/features/logs/task-utils";

describe("logAnalyzePasteSchema", () => {
  it("accepts valid paste payloads", () => {
    const result = logAnalyzePasteSchema.safeParse({
      content: "ERROR something failed",
      provider: "gemini",
      async_mode: false,
      workspace: "personal",
    });
    expect(result.success).toBe(true);
  });

  it("rejects empty or oversized content", () => {
    expect(
      logAnalyzePasteSchema.safeParse({
        content: "",
        provider: "gemini",
        async_mode: false,
        workspace: "personal",
      }).success,
    ).toBe(false);

    expect(
      logAnalyzePasteSchema.safeParse({
        content: "x".repeat(LOG_CONTENT_MAX + 1),
        provider: "gemini",
        async_mode: true,
        workspace: "personal",
      }).success,
    ).toBe(false);
  });
});

describe("logAnalyzeResultSchema", () => {
  it("parses a typical analysis result", () => {
    const result = logAnalyzeResultSchema.safeParse({
      summary: "Crash loop",
      severity: "high",
      detected_errors: ["OOMKilled"],
      possible_causes: ["Memory limit too low"],
      recommended_actions: ["Increase memory"],
      diagnostic_commands: ["kubectl describe pod x"],
      confidence: 0.82,
      disclaimer: "Review only",
    });
    expect(result.success).toBe(true);
  });
});

describe("taskPollInterval", () => {
  it("uses adaptive intervals for active tasks", () => {
    expect(taskPollInterval("queued")).toBe(2000);
    expect(taskPollInterval("running")).toBe(3000);
    expect(taskPollInterval("succeeded")).toBe(false);
    expect(taskPollInterval("failed")).toBe(false);
  });
});
