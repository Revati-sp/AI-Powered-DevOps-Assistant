import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { parseErrorResponse } from "@/lib/api/errors";
import { setAuthCookies, type AuthTokenPair } from "@/lib/auth/cookies";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type LoginBody = {
  username?: unknown;
  password?: unknown;
};

export async function POST(request: NextRequest) {
  let body: LoginBody;
  try {
    body = (await request.json()) as LoginBody;
  } catch {
    return NextResponse.json(
      {
        success: false,
        error: { code: "VALIDATION_ERROR", message: "Invalid JSON body" },
      },
      { status: 400 },
    );
  }

  const username = typeof body.username === "string" ? body.username.trim() : "";
  const password = typeof body.password === "string" ? body.password : "";

  if (!username || !password) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: "VALIDATION_ERROR",
          message: "Username and password are required",
        },
      },
      { status: 400 },
    );
  }

  const form = new URLSearchParams();
  form.set("username", username);
  form.set("password", password);

  const base = getApiBaseUrl().replace(/\/$/, "");
  const upstream = await fetch(`${base}${endpoints.auth.login()}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json",
    },
    body: form.toString(),
    cache: "no-store",
  });

  const text = await upstream.text();
  let json: unknown = null;
  if (text) {
    try {
      json = JSON.parse(text) as unknown;
    } catch {
      json = text;
    }
  }

  if (!upstream.ok) {
    const error = parseErrorResponse(upstream.status, json, upstream.headers);
    return NextResponse.json(
      {
        success: false,
        error: {
          code: error.code,
          message: error.message,
          details: error.details,
        },
      },
      {
        status: upstream.status,
        headers: error.requestId ? { "X-Request-ID": error.requestId } : undefined,
      },
    );
  }

  const tokens = json as AuthTokenPair;
  if (!tokens?.access_token || !tokens?.refresh_token) {
    return NextResponse.json(
      {
        success: false,
        error: { code: "UNKNOWN_ERROR", message: "Invalid login response" },
      },
      { status: 502 },
    );
  }

  await setAuthCookies({
    access_token: tokens.access_token,
    refresh_token: tokens.refresh_token,
    expires_in: tokens.expires_in ?? 900,
  });

  return NextResponse.json({
    success: true,
    expires_in: tokens.expires_in ?? 900,
  });
}
