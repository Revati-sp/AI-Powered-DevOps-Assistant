import { endpoints } from "@/lib/api/endpoints";
import { proxyAuthenticatedAuth } from "@/lib/auth/upstream";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  return proxyAuthenticatedAuth({
    method: "GET",
    upstreamPath: endpoints.auth.sessions(),
    includeRefreshHeader: true,
  });
}
