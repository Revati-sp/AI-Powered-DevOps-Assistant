import { logAnalyzeResultSchema, type ParsedLogAnalyzeResult } from "@/features/logs/schemas";
import type { TaskStatus } from "@/features/logs/types";

const ACTIVE: ReadonlySet<TaskStatus> = new Set(["queued", "running"]);

export function taskPollInterval(status: TaskStatus | undefined): number | false {
  if (status === "queued") return 2_000;
  if (status === "running") return 3_000;
  return false;
}

export function parseTaskLogResult(
  resultJson: Record<string, unknown> | null | undefined,
): ParsedLogAnalyzeResult | null {
  if (!resultJson) return null;
  const parsed = logAnalyzeResultSchema.safeParse(resultJson);
  return parsed.success ? parsed.data : null;
}

export function isTaskActive(status: TaskStatus | undefined): boolean {
  return status !== undefined && ACTIVE.has(status);
}
