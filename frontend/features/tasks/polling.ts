import type { TaskStatus } from "./types";

const ACTIVE_STATUSES: ReadonlySet<TaskStatus> = new Set(["queued", "running"]);

export function isActiveTaskStatus(status: TaskStatus | string): boolean {
  return ACTIVE_STATUSES.has(status as TaskStatus);
}

/**
 * Adaptive polling: faster while tasks are running, slower when only queued,
 * disabled when nothing is active.
 */
export function getTasksRefetchInterval(
  statuses: readonly (TaskStatus | string)[],
): number | false {
  const active = statuses.filter(isActiveTaskStatus);
  if (active.length === 0) {
    return false;
  }
  if (active.some((status) => status === "running")) {
    return 3_000;
  }
  return 8_000;
}
