import { NextRequest, NextResponse } from "next/server";

import { endpoints } from "@/lib/api/endpoints";
import { proxyPublicAuthPost } from "@/lib/auth/upstream";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type ForgotPasswordBody = {
  email?: unknown;
};

export async function POST(request: NextRequest) {
  let body: ForgotPasswordBody;
  try {
    body = (await request.json()) as ForgotPasswordBody;
  } catch {
    return NextResponse.json(
      {
        success: false,
        error: { code: "VALIDATION_ERROR", message: "Invalid JSON body" },
      },
      { status: 400 },
    );
  }

  const email = typeof body.email === "string" ? body.email.trim() : "";
  if (!email) {
    return NextResponse.json(
      {
        success: false,
        error: { code: "VALIDATION_ERROR", message: "Email is required" },
      },
      { status: 400 },
    );
  }

  return proxyPublicAuthPost(endpoints.auth.forgotPassword(), { email });
}
