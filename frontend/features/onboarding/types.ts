export type UserOnboardingResponse = {
  user_id: string;
  welcome_dismissed: boolean;
  profile_completed: boolean;
  first_chat_completed: boolean;
  first_artifact_created: boolean;
  organization_created: boolean;
  invite_team_completed: boolean;
  tour_completed: boolean;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
};

export type UserOnboardingPatchRequest = {
  welcome_dismissed?: boolean;
  profile_completed?: boolean;
  first_chat_completed?: boolean;
  first_artifact_created?: boolean;
  organization_created?: boolean;
  invite_team_completed?: boolean;
  tour_completed?: boolean;
  onboarding_completed?: boolean;
};

export type OnboardingChecklistKey =
  | "welcome_dismissed"
  | "profile_completed"
  | "first_chat_completed"
  | "first_artifact_created"
  | "organization_created"
  | "invite_team_completed"
  | "tour_completed";
