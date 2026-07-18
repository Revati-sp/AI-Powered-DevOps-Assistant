const UNITS = ["B", "KB", "MB", "GB", "TB", "PB"] as const;

/**
 * Human-readable byte size (binary units, base 1024).
 */
export function formatBytes(bytes: number, decimals = 1): string {
  if (!Number.isFinite(bytes) || bytes < 0) {
    return "0 B";
  }
  if (bytes === 0) {
    return "0 B";
  }

  const precision = Math.max(0, decimals);
  const unitIndex = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), UNITS.length - 1);
  const value = bytes / 1024 ** unitIndex;
  const formatted =
    precision === 0
      ? String(Math.round(value))
      : value
          .toFixed(precision)
          .replace(/\.0+$/, "")
          .replace(/(\.\d*[1-9])0+$/, "$1");

  return `${formatted} ${UNITS[unitIndex]}`;
}
