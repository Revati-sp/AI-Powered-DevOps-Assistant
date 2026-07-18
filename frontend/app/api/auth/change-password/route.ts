import { NextRequest, NextResponse } from "next/server";

import { endpoints } from "@/lib/api/endpoints";
import { PASSWORD_MIN } from "@/lib/constants/app";
import { proxyAuthenticatedAuth } from "@/lib/auth/upstream";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type ChangePasswordBody = {
  current_password?: unknown;
  new_password?: unknown;
};

export async function POST(request: NextRequest) {
  let body: ChangePasswordBody;
  try {
    body = (await request.json()) as ChangePasswordBody;
  } catch {
    return NextResponse.json(
      {
        success: false,
        error: { code: "VALIDATION_ERROR", message: "Invalid JSON body" },
      },
      { status: 400 },
    );
  }

  const currentPassword =
    typeof body.current_password === "string" ? body.current_password : "";
  const newPassword = typeof body.new_password === "string" ? body.new_password : "";

  if (!currentPassword) {
    return NextResponse.json(
      {
        success: false,
        error: { code: "VALIDATION_ERROR", message: "Current password is required" },
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

  return proxyAuthenticatedAuth({
    method: "POST",
    upstreamPath: endpoints.auth.changePassword(),
    body: {
      current_password: currentPassword,
      new_password: newPassword,
    },
    includeRefreshHeader: true,
  });
}
