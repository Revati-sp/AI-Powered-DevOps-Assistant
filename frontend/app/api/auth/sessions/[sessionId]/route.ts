import { NextRequest, NextResponse } from "next/server";

import { endpoints } from "@/lib/api/endpoints";
import { proxyAuthenticatedAuth } from "@/lib/auth/upstream";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = {
  params: Promise<{ sessionId: string }>;
};

export async function DELETE(_request: NextRequest, context: RouteContext) {
  const { sessionId } = await context.params;
  const trimmed = sessionId?.trim();

  if (!trimmed) {
    return NextResponse.json(
      {
        success: false,
        error: { code: "VALIDATION_ERROR", message: "Session id is required" },
      },
      { status: 400 },
    );
  }

  return proxyAuthenticatedAuth({
    method: "DELETE",
    upstreamPath: endpoints.auth.session(trimmed),
  });
}
