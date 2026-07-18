import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl, unwrapData } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { parseErrorResponse } from "@/lib/api/errors";
import type { components } from "@/lib/api/generated-types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RegisterRequest = components["schemas"]["RegisterRequest"];
type UserResponse = components["schemas"]["UserResponse"];

export async function POST(request: NextRequest) {
  let body: RegisterRequest;
  try {
    body = (await request.json()) as RegisterRequest;
  } catch {
    return NextResponse.json(
      {
        success: false,
        error: { code: "VALIDATION_ERROR", message: "Invalid JSON body" },
      },
      { status: 400 },
    );
  }

  const base = getApiBaseUrl().replace(/\/$/, "");
  const upstream = await fetch(`${base}${endpoints.auth.register()}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
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
      { status: upstream.status },
    );
  }

  const user = unwrapData<UserResponse>(json);
  return NextResponse.json({ success: true, data: user });
}
