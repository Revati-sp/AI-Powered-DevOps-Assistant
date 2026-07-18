import { describe, expect, it } from "vitest";

import {
  computeOnboardingProgress,
  isChecklistItemDone,
  ONBOARDING_CHECKLIST_ITEMS,
} from "@/features/onboarding/progress";
import type { UserOnboardingResponse } from "@/features/onboarding/types";

const sample: UserOnboardingResponse = {
  user_id: "u1",
  welcome_dismissed: true,
  profile_completed: false,
  first_chat_completed: true,
  first_artifact_created: false,
  organization_created: false,
  invite_team_completed: false,
  tour_completed: false,
  onboarding_completed: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("onboarding progress helpers", () => {
  it("exposes a stable checklist length", () => {
    expect(ONBOARDING_CHECKLIST_ITEMS.length).toBeGreaterThan(0);
  });

  it("computes percent from completed flags", () => {
    const progress = computeOnboardingProgress(sample);
    expect(progress.completed).toBe(2);
    expect(progress.total).toBe(ONBOARDING_CHECKLIST_ITEMS.length);
  });

  it("checks individual checklist keys", () => {
    expect(isChecklistItemDone(sample, "welcome_dismissed")).toBe(true);
    expect(isChecklistItemDone(sample, "profile_completed")).toBe(false);
  });
});
