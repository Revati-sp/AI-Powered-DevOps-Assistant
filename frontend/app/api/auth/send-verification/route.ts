import { endpoints } from "@/lib/api/endpoints";
import { proxyAuthenticatedAuth } from "@/lib/auth/upstream";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST() {
  return proxyAuthenticatedAuth({
    method: "POST",
    upstreamPath: endpoints.auth.sendVerification(),
  });
}
