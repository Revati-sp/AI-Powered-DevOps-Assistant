/**
 * Allow only same-origin relative paths for post-login redirects.
 * Rejects protocol-relative URLs (`//evil.com`) and absolute URLs.
 */
export function getSafeReturnUrl(
  value: string | null | undefined,
  fallback = "/dashboard",
): string {
  if (typeof value !== "string") {
    return fallback;
  }

  const trimmed = value.trim();
  if (!trimmed.startsWith("/") || trimmed.startsWith("//")) {
    return fallback;
  }

  // Extra hardening against open-redirect tricks.
  if (trimmed.includes("\\") || trimmed.includes("://") || trimmed.includes("\0")) {
    return fallback;
  }

  return trimmed;
}
