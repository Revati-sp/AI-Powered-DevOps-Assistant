import { NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { parseErrorResponse } from "@/lib/api/errors";
import {
  clearAuthCookies,
  getAccessToken,
  getRefreshToken,
  setAuthCookies,
  type AuthTokenPair,
} from "@/lib/auth/cookies";

async function parseResponseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function errorJsonResponse(status: number, json: unknown, headers?: Headers): NextResponse {
  const error = parseErrorResponse(status, json, headers);
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
      status,
      headers: error.requestId ? { "X-Request-ID": error.requestId } : undefined,
    },
  );
}

async function tryRefreshTokens(): Promise<string | null> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const base = getApiBaseUrl().replace(/\/$/, "");
    const response = await fetch(`${base}${endpoints.auth.refresh()}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    });

    if (!response.ok) {
      await clearAuthCookies();
      return null;
    }

    const pair = (await response.json()) as AuthTokenPair;
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

/** Proxy unauthenticated auth POST requests to the backend API. */
export async function proxyPublicAuthPost(
  upstreamPath: string,
  body: unknown,
): Promise<NextResponse> {
  const base = getApiBaseUrl().replace(/\/$/, "");
  const upstream = await fetch(`${base}${upstreamPath}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const json = await parseResponseBody(upstream);
  if (!upstream.ok) {
    return errorJsonResponse(upstream.status, json, upstream.headers);
  }

  return NextResponse.json(json);
}

/** Proxy authenticated auth requests; refresh cookie is attached server-side when requested. */
export async function proxyAuthenticatedAuth(options: {
  method: string;
  upstreamPath: string;
  body?: unknown;
  includeRefreshHeader?: boolean;
}): Promise<NextResponse> {
  const { method, upstreamPath, body, includeRefreshHeader = false } = options;
  let accessToken = await getAccessToken();
  const refreshToken = includeRefreshHeader ? await getRefreshToken() : undefined;

  const send = async (token: string | undefined): Promise<Response> => {
    const headers: Record<string, string> = {
      Accept: "application/json",
    };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    if (refreshToken) {
      headers["X-Refresh-Token"] = refreshToken;
    }
    if (body !== undefined && method !== "GET" && method !== "HEAD") {
      headers["Content-Type"] = "application/json";
    }

    const base = getApiBaseUrl().replace(/\/$/, "");
    return fetch(`${base}${upstreamPath}`, {
      method,
      headers,
      body:
        body !== undefined && method !== "GET" && method !== "HEAD"
          ? JSON.stringify(body)
          : undefined,
      cache: "no-store",
    });
  };

  let upstream = await send(accessToken);
  if (upstream.status === 401) {
    const nextAccess = await tryRefreshTokens();
    if (!nextAccess) {
      await clearAuthCookies();
      return NextResponse.json(
        {
          success: false,
          error: { code: "UNAUTHORIZED", message: "Session expired" },
        },
        { status: 401 },
      );
    }
    accessToken = nextAccess;
    upstream = await send(accessToken);
  }

  const json = await parseResponseBody(upstream);
  if (!upstream.ok) {
    return errorJsonResponse(upstream.status, json, upstream.headers);
  }

  return NextResponse.json(json);
}
