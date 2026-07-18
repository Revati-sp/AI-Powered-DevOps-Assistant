import { NextRequest, NextResponse } from "next/server";

import {
  clearAuthCookies,
  getAccessToken,
  getRefreshToken,
  setAuthCookies,
  type AuthTokenPair,
} from "@/lib/auth/cookies";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const RETRY_HEADER = "x-bff-retry";

const FORWARD_REQUEST_HEADERS = [
  "content-type",
  "accept",
  "idempotency-key",
  "x-request-id",
] as const;

const FORWARD_RESPONSE_HEADERS = [
  "content-type",
  "cache-control",
  "connection",
  "x-request-id",
  "retry-after",
] as const;

function getBackendBaseUrl(): string {
  return (
    process.env.INTERNAL_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000"
  ).replace(/\/$/, "");
}

function buildBackendUrl(pathSegments: string[], search: string): string {
  // Segments from Next.js are already decoded; join as-is for the upstream path.
  const path = pathSegments.join("/");
  return `${getBackendBaseUrl()}/${path}${search}`;
}

function isSseRequest(request: NextRequest, pathSegments: string[]): boolean {
  const accept = request.headers.get("accept") ?? "";
  if (accept.includes("text/event-stream")) {
    return true;
  }
  return pathSegments.join("/").includes("chat/stream");
}

function pickForwardHeaders(source: Headers, names: readonly string[]): Headers {
  const headers = new Headers();
  for (const name of names) {
    const value = source.get(name);
    if (value) {
      headers.set(name, value);
    }
  }
  return headers;
}

function responseHeadersFromUpstream(upstream: Response): Headers {
  return pickForwardHeaders(upstream.headers, FORWARD_RESPONSE_HEADERS);
}

async function tryRefreshTokens(): Promise<string | null> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch(`${getBackendBaseUrl()}/api/v1/auth/refresh`, {
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

async function proxyToBackend(options: {
  request: NextRequest;
  pathSegments: string[];
  accessToken: string | undefined;
  body: ArrayBuffer | undefined;
  isRetry: boolean;
}): Promise<Response> {
  const { request, pathSegments, accessToken, body, isRetry } = options;
  const backendUrl = buildBackendUrl(pathSegments, request.nextUrl.search);
  const headers = pickForwardHeaders(request.headers, FORWARD_REQUEST_HEADERS);

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  if (isRetry) {
    headers.set(RETRY_HEADER, "1");
  }

  const method = request.method.toUpperCase();
  const init: RequestInit = {
    method,
    headers,
    cache: "no-store",
  };

  if (method !== "GET" && method !== "HEAD" && body !== undefined && body.byteLength > 0) {
    init.body = body;
  }

  return fetch(backendUrl, init);
}

async function handle(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  const pathSegments = path ?? [];
  const alreadyRetried = request.headers.get(RETRY_HEADER) === "1";
  const sse = isSseRequest(request, pathSegments);
  const method = request.method.toUpperCase();

  // Buffer request body once so a 401 → refresh → retry can re-send it.
  // Response streaming for SSE is unaffected (body is not buffered).
  let requestBody: ArrayBuffer | undefined;
  if (method !== "GET" && method !== "HEAD") {
    requestBody = await request.arrayBuffer();
  }

  let accessToken = await getAccessToken();
  let upstream = await proxyToBackend({
    request,
    pathSegments,
    accessToken,
    body: requestBody,
    isRetry: alreadyRetried,
  });

  // Refresh once on 401 only — never on 403, never when already retried.
  if (upstream.status === 401 && !alreadyRetried) {
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
    upstream = await proxyToBackend({
      request,
      pathSegments,
      accessToken,
      body: requestBody,
      isRetry: true,
    });
  }

  // Pass through SSE / event-stream bodies without buffering.
  if (sse) {
    return new NextResponse(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeadersFromUpstream(upstream),
    });
  }

  const responseBody = await upstream.arrayBuffer();
  return new NextResponse(responseBody, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeadersFromUpstream(upstream),
  });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handle(request, context);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handle(request, context);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handle(request, context);
}

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return handle(request, context);
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return handle(request, context);
}
