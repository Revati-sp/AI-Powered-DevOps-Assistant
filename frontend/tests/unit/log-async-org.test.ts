import { describe, expect, it, vi } from "vitest";

import { analyzeLogsAsync } from "@/features/logs/api";
import { logAnalyzePasteSchema } from "@/features/logs/schemas";

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(async (_path: string, options?: { body?: Record<string, unknown> }) => {
    return {
      task_id: "task-1",
      status: "queued",
      organization_id: options?.body?.organization_id ?? null,
      analysis_id: "analysis-1",
    };
  }),
}));

describe("async log organization scope", () => {
  it("accepts personal workspace selection", () => {
    const parsed = logAnalyzePasteSchema.parse({
      content: "ERROR failed",
      provider: "gemini",
      async_mode: true,
      workspace: "personal",
    });
    expect(parsed.workspace).toBe("personal");
  });

  it("sends organization_id only when provided", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    await analyzeLogsAsync({
      content: "CrashLoopBackOff",
      provider: "gemini",
      organization_id: "11111111-1111-1111-1111-111111111111",
    });
    expect(apiFetch).toHaveBeenCalledWith(
      expect.stringContaining("/logs/analyze/async"),
      expect.objectContaining({
        body: expect.objectContaining({
          organization_id: "11111111-1111-1111-1111-111111111111",
        }),
      }),
    );

    await analyzeLogsAsync({
      content: "CrashLoopBackOff",
      provider: "gemini",
    });
    expect(apiFetch).toHaveBeenLastCalledWith(
      expect.stringContaining("/logs/analyze/async"),
      expect.objectContaining({
        body: expect.not.objectContaining({
          organization_id: expect.anything(),
        }),
      }),
    );
  });
});
