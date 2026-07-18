import { redirect } from "next/navigation";

import { getAccessToken, getRefreshToken } from "@/lib/auth/cookies";

export default async function HomePage() {
  const [access, refresh] = await Promise.all([getAccessToken(), getRefreshToken()]);

  if (access || refresh) {
    redirect("/dashboard");
  }

  redirect("/login");
}
