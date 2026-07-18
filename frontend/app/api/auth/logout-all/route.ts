import { NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { clearAuthCookies, getAccessToken } from "@/lib/auth/cookies";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST() {
  const accessToken = await getAccessToken();

  if (accessToken) {
    try {
      const base = getApiBaseUrl().replace(/\/$/, "");
      await fetch(`${base}${endpoints.auth.logoutAll()}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Accept: "application/json",
        },
        cache: "no-store",
      });
    } catch {
      // Still clear local session cookies.
    }
  }

  await clearAuthCookies();
  return NextResponse.json({ success: true });
}
