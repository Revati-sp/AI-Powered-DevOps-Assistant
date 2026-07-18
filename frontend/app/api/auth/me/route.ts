import { NextResponse } from "next/server";

import { getCurrentUser } from "@/lib/auth/session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const user = await getCurrentUser();

  if (!user) {
    return NextResponse.json(
      {
        success: false,
        error: { code: "UNAUTHORIZED", message: "Not authenticated" },
      },
      { status: 401 },
    );
  }

  return NextResponse.json({ success: true, data: user });
}
