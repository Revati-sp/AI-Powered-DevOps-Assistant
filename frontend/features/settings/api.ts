import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { components } from "@/lib/api/generated-types";

export type UserResponse = components["schemas"]["UserResponse"];

/** Display-only profile via BFF. */
export function fetchProfile(): Promise<UserResponse> {
  return apiFetch<UserResponse>(endpoints.users.me());
}
