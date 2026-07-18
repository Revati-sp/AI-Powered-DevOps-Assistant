import { NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { clearAuthCookies, getRefreshToken } from "@/lib/auth/cookies";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST() {
  const refreshToken = await getRefreshToken();

  if (refreshToken) {
    try {
      const base = getApiBaseUrl().replace(/\/$/, "");
      await fetch(`${base}${endpoints.auth.logout()}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
        cache: "no-store",
      });
    } catch {
      // Still clear local session cookies.
    }
  }

  await clearAuthCookies();
  return NextResponse.json({ success: true });
}
