import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { components } from "@/lib/api/generated-types";

export type UserResponse = components["schemas"]["UserResponse"] & {
  display_name?: string | null;
  timezone?: string | null;
  job_title?: string | null;
  avatar_url?: string | null;
};

export type UpdateProfileRequest = {
  username?: string;
  display_name?: string | null;
  timezone?: string | null;
  job_title?: string | null;
  avatar_url?: string | null;
};

/** Display-only profile via BFF. */
export function fetchProfile(): Promise<UserResponse> {
  return apiFetch<UserResponse>(endpoints.users.me());
}

export function updateProfile(body: UpdateProfileRequest): Promise<UserResponse> {
  return apiFetch<UserResponse>(endpoints.users.me(), { method: "PATCH", body });
}
