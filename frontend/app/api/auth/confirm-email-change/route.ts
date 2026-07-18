import { NextRequest, NextResponse } from "next/server";

import { endpoints } from "@/lib/api/endpoints";
import { proxyPublicAuthPost } from "@/lib/auth/upstream";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type ConfirmEmailChangeBody = {
  token?: unknown;
};

export async function POST(request: NextRequest) {
  let body: ConfirmEmailChangeBody;
  try {
    body = (await request.json()) as ConfirmEmailChangeBody;
  } catch {
    return NextResponse.json(
      {
        success: false,
        error: { code: "VALIDATION_ERROR", message: "Invalid JSON body" },
      },
      { status: 400 },
    );
  }

  const token = typeof body.token === "string" ? body.token.trim() : "";
  if (!token) {
    return NextResponse.json(
      {
        success: false,
        error: { code: "VALIDATION_ERROR", message: "Confirmation token is required" },
      },
      { status: 400 },
    );
  }

  return proxyPublicAuthPost(endpoints.users.emailChangeConfirm(), { token });
}
