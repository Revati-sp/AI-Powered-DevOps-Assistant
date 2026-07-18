import type { OnboardingChecklistKey, UserOnboardingResponse } from "./types";

export type OnboardingChecklistItem = {
  key: OnboardingChecklistKey;
  label: string;
  description: string;
  href: string;
};

export const ONBOARDING_CHECKLIST_ITEMS: OnboardingChecklistItem[] = [
  {
    key: "welcome_dismissed",
    label: "Dismiss welcome banner",
    description: "Close the dashboard welcome message when you're ready.",
    href: "/dashboard",
  },
  {
    key: "profile_completed",
    label: "Review your profile",
    description: "Confirm your account details in settings.",
    href: "/settings/profile",
  },
  {
    key: "first_chat_completed",
    label: "Start a chat",
    description: "Ask the assistant a DevOps question.",
    href: "/chat",
  },
  {
    key: "first_artifact_created",
    label: "Create an artifact",
    description: "Save generated configs for version control.",
    href: "/artifacts",
  },
  {
    key: "organization_created",
    label: "Create or join an organization",
    description: "Set up a workspace for your team.",
    href: "/organizations",
  },
  {
    key: "invite_team_completed",
    label: "Invite a teammate",
    description: "Collaborate with others in your organization.",
    href: "/organizations",
  },
  {
    key: "tour_completed",
    label: "Complete the product tour",
    description: "Mark the tour done when you've explored the app.",
    href: "/onboarding",
  },
];

export type OnboardingProgress = {
  completed: number;
  total: number;
  percent: number;
  isComplete: boolean;
};

export function computeOnboardingProgress(
  onboarding: UserOnboardingResponse | undefined,
): OnboardingProgress {
  const total = ONBOARDING_CHECKLIST_ITEMS.length;
  if (!onboarding) {
    return { completed: 0, total, percent: 0, isComplete: false };
  }

  const completed = ONBOARDING_CHECKLIST_ITEMS.filter((item) => onboarding[item.key]).length;
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

  return {
    completed,
    total,
    percent,
    isComplete: onboarding.onboarding_completed || completed === total,
  };
}

export function isChecklistItemDone(
  onboarding: UserOnboardingResponse | undefined,
  key: OnboardingChecklistKey,
): boolean {
  return Boolean(onboarding?.[key]);
}
