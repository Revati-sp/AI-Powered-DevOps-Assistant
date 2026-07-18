import { cookies } from "next/headers";

export const ACCESS_COOKIE = "ada_access";
export const REFRESH_COOKIE = "ada_refresh";

const REFRESH_MAX_AGE_SECONDS = 14 * 24 * 60 * 60;

export type AuthTokenPair = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
};

function isCookieSecure(): boolean {
  const raw = process.env.AUTH_COOKIE_SECURE;
  if (raw === "true" || raw === "1") {
    return true;
  }
  if (raw === "false" || raw === "0") {
    return false;
  }
  return process.env.NODE_ENV === "production";
}

function cookieSameSite(): "lax" | "strict" | "none" {
  const raw = (process.env.AUTH_COOKIE_SAMESITE || "lax").toLowerCase();
  if (raw === "strict" || raw === "none" || raw === "lax") {
    return raw;
  }
  return "lax";
}

function cookieDomain(): string | undefined {
  const domain = process.env.AUTH_COOKIE_DOMAIN?.trim();
  return domain ? domain : undefined;
}

function baseCookieOptions(maxAge: number) {
  const domain = cookieDomain();
  return {
    httpOnly: true,
    secure: isCookieSecure(),
    sameSite: cookieSameSite(),
    path: "/",
    maxAge,
    ...(domain ? { domain } : {}),
  };
}

export async function setAuthCookies(tokens: AuthTokenPair): Promise<void> {
  const jar = await cookies();
  const accessMaxAge = Math.max(1, Math.floor(tokens.expires_in));

  jar.set(ACCESS_COOKIE, tokens.access_token, baseCookieOptions(accessMaxAge));
  jar.set(REFRESH_COOKIE, tokens.refresh_token, baseCookieOptions(REFRESH_MAX_AGE_SECONDS));
}

export async function clearAuthCookies(): Promise<void> {
  const jar = await cookies();
  jar.set(ACCESS_COOKIE, "", { ...baseCookieOptions(0), maxAge: 0 });
  jar.set(REFRESH_COOKIE, "", { ...baseCookieOptions(0), maxAge: 0 });
}

export async function getAccessToken(): Promise<string | undefined> {
  const jar = await cookies();
  return jar.get(ACCESS_COOKIE)?.value;
}

export async function getRefreshToken(): Promise<string | undefined> {
  const jar = await cookies();
  return jar.get(REFRESH_COOKIE)?.value;
}
