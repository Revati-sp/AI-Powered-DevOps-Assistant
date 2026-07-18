const REDACTED_KEY_PATTERN =
  /(password|secret|token|api[_-]?key|authorization|credential|private[_-]?key)/i;

/**
 * Recursively label redacted / sensitive metadata values for display.
 */
export function labelRedactedMetadata(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => labelRedactedMetadata(item));
  }
  if (value !== null && typeof value === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, nested] of Object.entries(value as Record<string, unknown>)) {
      if (REDACTED_KEY_PATTERN.test(key)) {
        result[key] = "[REDACTED]";
        continue;
      }
      if (typeof nested === "string" && (nested === "[REDACTED]" || nested === "***")) {
        result[key] = "[REDACTED]";
        continue;
      }
      result[key] = labelRedactedMetadata(nested);
    }
    return result;
  }
  if (typeof value === "string" && (value === "[REDACTED]" || value === "***")) {
    return "[REDACTED]";
  }
  return value;
}
