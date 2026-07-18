/**
 * Sanitize a user- or server-provided name for safe Content-Disposition filenames.
 * Strips path segments, null bytes, and characters unsafe on common filesystems.
 */
export function sanitizeFilename(name: string, fallback = "download.txt"): string {
  if (typeof name !== "string" || name.length === 0) {
    return fallback;
  }

  let base = name.replaceAll("\0", "").replaceAll("\\", "/");
  const segments = base.split("/");
  base = segments[segments.length - 1] ?? "";

  // Control chars, path/reserved chars, and other dangerous filesystem tokens.
  base = base
    .replace(/[\u0000-\u001f\u007f]/g, "")
    .replace(/[<>:"|?*]/g, "_")
    .replace(/^\.+/u, "")
    .trim();

  if (!base || base === "." || base === "..") {
    return fallback;
  }

  const maxLen = 200;
  if (base.length > maxLen) {
    const dot = base.lastIndexOf(".");
    const ext = dot > 0 && dot > base.length - 12 ? base.slice(dot) : "";
    const stem = base.slice(0, maxLen - ext.length);
    base = `${stem}${ext}`;
  }

  return base || fallback;
}
