import { describe, expect, it } from "vitest";

import {
  computeOnboardingProgress,
  isChecklistItemDone,
  ONBOARDING_CHECKLIST_ITEMS,
} from "@/features/onboarding/progress";
import type { UserOnboardingResponse } from "@/features/onboarding/types";
import { getUsageLimitStatus, quotaFormSchema } from "@/features/usage/schemas";

const baseOnboarding: UserOnboardingResponse = {
  user_id: "user-1",
  welcome_dismissed: false,
  profile_completed: false,
  first_chat_completed: false,
  first_artifact_created: false,
  organization_created: false,
  invite_team_completed: false,
  tour_completed: false,
  onboarding_completed: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("quotaFormSchema", () => {
  it("accepts valid quota values", () => {
    const result = quotaFormSchema.safeParse({
      daily_token_limit: 1000,
      daily_request_limit: 50,
      monthly_token_limit: 20000,
      monthly_request_limit: 500,
      enforce_quotas: true,
    });
    expect(result.success).toBe(true);
  });

  it("accepts empty limits as null", () => {
    const result = quotaFormSchema.safeParse({
      daily_token_limit: null,
      daily_request_limit: null,
      monthly_token_limit: null,
      monthly_request_limit: null,
      enforce_quotas: false,
    });
    expect(result.success).toBe(true);
  });

  it("rejects negative limits", () => {
    const result = quotaFormSchema.safeParse({
      daily_token_limit: -1,
      enforce_quotas: true,
    });
    expect(result.success).toBe(false);
  });
});

describe("getUsageLimitStatus", () => {
  it("returns ok when no limit is set", () => {
    expect(getUsageLimitStatus(100, null)).toBe("ok");
  });

  it("returns warning when above 80% of limit", () => {
    expect(getUsageLimitStatus(85, 100)).toBe("warning");
  });

  it("returns over when at or above limit", () => {
    expect(getUsageLimitStatus(100, 100)).toBe("over");
    expect(getUsageLimitStatus(150, 100)).toBe("over");
  });
});

describe("computeOnboardingProgress", () => {
  it("returns zero progress when onboarding is undefined", () => {
    expect(computeOnboardingProgress(undefined)).toEqual({
      completed: 0,
      total: ONBOARDING_CHECKLIST_ITEMS.length,
      percent: 0,
      isComplete: false,
    });
  });

  it("counts completed checklist items", () => {
    const progress = computeOnboardingProgress({
      ...baseOnboarding,
      welcome_dismissed: true,
      profile_completed: true,
      first_chat_completed: true,
    });
    expect(progress.completed).toBe(3);
    expect(progress.percent).toBe(
      Math.round((3 / ONBOARDING_CHECKLIST_ITEMS.length) * 100),
    );
  });

  it("marks complete when onboarding_completed is true", () => {
    const progress = computeOnboardingProgress({
      ...baseOnboarding,
      onboarding_completed: true,
    });
    expect(progress.isComplete).toBe(true);
  });
});

describe("isChecklistItemDone", () => {
  it("returns false for incomplete items", () => {
    expect(isChecklistItemDone(baseOnboarding, "tour_completed")).toBe(false);
  });

  it("returns true for completed items", () => {
    expect(
      isChecklistItemDone({ ...baseOnboarding, tour_completed: true }, "tour_completed"),
    ).toBe(true);
  });
});
