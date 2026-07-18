/**
 * Build a query string from a filter object, omitting null/undefined/empty values.
 */
export function buildQueryString(
  params: Record<string, string | number | boolean | null | undefined>,
): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}
