import { format, formatDistanceToNow, isValid, parseISO } from "date-fns";

function toDate(value: string | number | Date): Date {
  if (value instanceof Date) {
    return value;
  }
  if (typeof value === "number") {
    return new Date(value);
  }
  const parsed = parseISO(value);
  return isValid(parsed) ? parsed : new Date(value);
}

export function formatDateTime(value: string | number | Date): string {
  const date = toDate(value);
  if (!isValid(date)) {
    return "";
  }
  return format(date, "MMM d, yyyy HH:mm");
}

export function formatRelative(value: string | number | Date): string {
  const date = toDate(value);
  if (!isValid(date)) {
    return "";
  }
  return formatDistanceToNow(date, { addSuffix: true });
}
