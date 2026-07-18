import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { isApiClientError } from "@/lib/api/errors";
import type { components } from "@/lib/api/generated-types";
import {
  clearAuthCookies,
  getAccessToken,
  getRefreshToken,
  setAuthCookies,
  type AuthTokenPair,
} from "@/lib/auth/cookies";

export type CurrentUser = components["schemas"]["UserResponse"];

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const pair = await apiFetch<AuthTokenPair>(endpoints.auth.refresh(), {
      method: "POST",
      body: { refresh_token: refreshToken },
      raw: true,
    });

    if (!pair?.access_token || !pair?.refresh_token) {
      await clearAuthCookies();
      return null;
    }

    await setAuthCookies({
      access_token: pair.access_token,
      refresh_token: pair.refresh_token,
      expires_in: pair.expires_in ?? 900,
    });

    return pair.access_token;
  } catch {
    await clearAuthCookies();
    return null;
  }
}

/**
 * Server helper: load the current user via `/users/me`.
 * On 401, attempts a single refresh using the HTTP-only refresh cookie.
 */
export async function getCurrentUser(): Promise<CurrentUser | null> {
  let accessToken = await getAccessToken();
  if (!accessToken) {
    accessToken = (await refreshAccessToken()) ?? undefined;
    if (!accessToken) {
      return null;
    }
  }

  try {
    return await apiFetch<CurrentUser>(endpoints.users.me(), {
      accessToken,
    });
  } catch (error) {
    if (!isApiClientError(error) || error.status !== 401) {
      return null;
    }

    const nextAccess = await refreshAccessToken();
    if (!nextAccess) {
      return null;
    }

    try {
      return await apiFetch<CurrentUser>(endpoints.users.me(), {
        accessToken: nextAccess,
      });
    } catch {
      return null;
    }
  }
}
