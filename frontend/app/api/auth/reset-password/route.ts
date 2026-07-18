import { NextRequest, NextResponse } from "next/server";

import { endpoints } from "@/lib/api/endpoints";
import { PASSWORD_MIN } from "@/lib/constants/app";
import { proxyPublicAuthPost } from "@/lib/auth/upstream";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type ResetPasswordBody = {
  token?: unknown;
  new_password?: unknown;
};

export async function POST(request: NextRequest) {
  let body: ResetPasswordBody;
  try {
    body = (await request.json()) as ResetPasswordBody;
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
  const newPassword = typeof body.new_password === "string" ? body.new_password : "";

  if (!token) {
    return NextResponse.json(
      {
        success: false,
        error: { code: "VALIDATION_ERROR", message: "Reset token is required" },
      },
      { status: 400 },
    );
  }

  if (!newPassword || newPassword.length < PASSWORD_MIN) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: "VALIDATION_ERROR",
          message: `Password must be at least ${PASSWORD_MIN} characters`,
        },
      },
      { status: 400 },
    );
  }

  return proxyPublicAuthPost(endpoints.auth.resetPassword(), {
    token,
    new_password: newPassword,
  });
}
