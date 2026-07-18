import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";

import type { UserOnboardingPatchRequest, UserOnboardingResponse } from "./types";

export function fetchOnboarding(): Promise<UserOnboardingResponse> {
  return apiFetch<UserOnboardingResponse>(endpoints.users.meOnboarding());
}

export function patchOnboarding(body: UserOnboardingPatchRequest): Promise<UserOnboardingResponse> {
  return apiFetch<UserOnboardingResponse>(endpoints.users.meOnboarding(), {
    method: "PATCH",
    body,
  });
}
