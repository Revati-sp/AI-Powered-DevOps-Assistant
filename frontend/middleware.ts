import { NextRequest, NextResponse } from "next/server";

import { getSafeReturnUrl } from "@/lib/utils/return-url";

/** Keep in sync with lib/auth/cookies.ts — do not import that module (uses next/headers). */
const ACCESS_COOKIE = "ada_access";
const REFRESH_COOKIE = "ada_refresh";

const PROTECTED_PREFIXES = [
  "/dashboard",
  "/chat",
  "/logs",
  "/generators",
  "/reviews",
  "/artifacts",
  "/organizations",
  "/tasks",
  "/settings",
] as const;

const AUTH_PAGES = new Set(["/login", "/register"]);

function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

function hasSessionCookies(request: NextRequest): boolean {
  return Boolean(
    request.cookies.get(ACCESS_COOKIE)?.value || request.cookies.get(REFRESH_COOKIE)?.value,
  );
}

function hasAccessCookie(request: NextRequest): boolean {
  return Boolean(request.cookies.get(ACCESS_COOKIE)?.value);
}

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  if (
    pathname.startsWith("/api/") ||
    pathname.startsWith("/_next/") ||
    pathname === "/favicon.ico" ||
    pathname === "/"
  ) {
    return NextResponse.next();
  }

  if (isProtectedPath(pathname) && !hasSessionCookies(request)) {
    const returnUrl = getSafeReturnUrl(`${pathname}${search}`);
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.search = `?returnUrl=${encodeURIComponent(returnUrl)}`;
    return NextResponse.redirect(loginUrl);
  }

  if (AUTH_PAGES.has(pathname) && hasAccessCookie(request)) {
    const dashboardUrl = request.nextUrl.clone();
    dashboardUrl.pathname = "/dashboard";
    dashboardUrl.search = "";
    return NextResponse.redirect(dashboardUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)"],
};
