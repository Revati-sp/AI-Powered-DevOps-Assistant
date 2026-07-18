import { describe, expect, it } from "vitest";

import {
  normalizeActivityItems,
  normalizeFindingCounts,
  normalizeTaskCounts,
} from "@/features/dashboard/api";

describe("dashboard response normalizers", () => {
  it("unwraps findings counts envelope and bare counts", () => {
    expect(
      normalizeFindingCounts({
        counts: { critical: 1, high: 2, medium: 3, low: 4 },
        items: [],
      }),
    ).toEqual({ critical: 1, high: 2, medium: 3, low: 4 });

    expect(normalizeFindingCounts({ critical: 0, high: 1, medium: 0, low: 0 })).toEqual({
      critical: 0,
      high: 1,
      medium: 0,
      low: 0,
    });
  });

  it("unwraps task counts envelope", () => {
    expect(
      normalizeTaskCounts({
        counts: { queued: 1, running: 0, succeeded: 2, failed: 0 },
        items: [],
      }),
    ).toEqual({ queued: 1, running: 0, succeeded: 2, failed: 0 });
  });

  it("unwraps activity items envelope and bare arrays", () => {
    const item = {
      id: "1",
      type: "task",
      title: "t",
      timestamp: "2026-01-01T00:00:00Z",
      route_target: "/tasks",
    };
    expect(normalizeActivityItems({ items: [item] })).toEqual([item]);
    expect(normalizeActivityItems([item])).toEqual([item]);
    expect(normalizeActivityItems(null)).toEqual([]);
  });
});
