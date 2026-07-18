import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { buildQueryString } from "@/lib/api/query-string";

export type DashboardFilters = {
  organization_id?: string | null;
  time_range?: "24h" | "7d" | "30d";
};

export type DashboardActivityItem = {
  id: string;
  type: string;
  title: string;
  timestamp: string;
  status?: string | null;
  organization_id?: string | null;
  route_target: string;
};

export type DashboardSummary = {
  conversations: { total: number; recent: number };
  artifacts: { total: number; favorites: number; archived: number };
  tasks: { queued: number; running: number; succeeded: number; failed: number };
  findings: { critical: number; high: number; medium: number; low: number };
  usage: { requests_used: number; requests_limit: number };
  organization: { member_count: number; active_policy_packs: number } | null;
};

export type DashboardTaskCounts = DashboardSummary["tasks"];

/** Backend envelopes for nested dashboard resources (APIResponse.data payloads). */
type DashboardActivityResponse = {
  items: DashboardActivityItem[];
};

type DashboardFindingsResponse = {
  counts: DashboardSummary["findings"];
  items?: unknown[];
};

type DashboardTasksResponse = {
  counts: DashboardTaskCounts;
  items?: unknown[];
};

export type DashboardSnapshot = {
  summary?: DashboardSummary;
  activity: DashboardActivityItem[];
  findings?: DashboardSummary["findings"];
  tasks?: DashboardTaskCounts;
  failures: {
    summary: boolean;
    activity: boolean;
    findings: boolean;
    tasks: boolean;
  };
};

function settledValue<T>(result: PromiseSettledResult<T>, fallback: T): T {
  return result.status === "fulfilled" ? result.value : fallback;
}

function isCountRecord(value: unknown): value is Record<string, number> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  return Object.values(value).every((entry) => typeof entry === "number");
}

/** Accept either bare counts or `{ counts: ... }` (including stale React Query cache). */
export function normalizeFindingCounts(
  value: unknown,
): DashboardSummary["findings"] | undefined {
  if (!value || typeof value !== "object") {
    return undefined;
  }
  const record = value as Record<string, unknown>;
  if (isCountRecord(record) && "critical" in record && "high" in record) {
    return {
      critical: Number(record.critical) || 0,
      high: Number(record.high) || 0,
      medium: Number(record.medium) || 0,
      low: Number(record.low) || 0,
    };
  }
  if ("counts" in record) {
    return normalizeFindingCounts(record.counts);
  }
  return undefined;
}

/** Accept either bare task counts or `{ counts: ... }`. */
export function normalizeTaskCounts(value: unknown): DashboardTaskCounts | undefined {
  if (!value || typeof value !== "object") {
    return undefined;
  }
  const record = value as Record<string, unknown>;
  if (isCountRecord(record) && "queued" in record && "running" in record) {
    return {
      queued: Number(record.queued) || 0,
      running: Number(record.running) || 0,
      succeeded: Number(record.succeeded) || 0,
      failed: Number(record.failed) || 0,
    };
  }
  if ("counts" in record) {
    return normalizeTaskCounts(record.counts);
  }
  return undefined;
}

export function normalizeActivityItems(value: unknown): DashboardActivityItem[] {
  if (Array.isArray(value)) {
    return value as DashboardActivityItem[];
  }
  if (value && typeof value === "object" && Array.isArray((value as { items?: unknown }).items)) {
    return (value as DashboardActivityResponse).items;
  }
  return [];
}

function dashboardUrl(path: string, filters: DashboardFilters) {
  return `${path}${buildQueryString({
    organization_id: filters.organization_id ?? undefined,
    time_range: filters.time_range ?? "7d",
  })}`;
}

export async function fetchDashboardSnapshot(
  filters: DashboardFilters = {},
): Promise<DashboardSnapshot> {
  const [summaryResult, activityResult, findingsResult, tasksResult] = await Promise.allSettled([
    apiFetch<DashboardSummary>(dashboardUrl(endpoints.dashboard.summary(), filters)),
    apiFetch<DashboardActivityResponse>(dashboardUrl(endpoints.dashboard.activity(), filters)),
    apiFetch<DashboardFindingsResponse>(dashboardUrl(endpoints.dashboard.findings(), filters)),
    apiFetch<DashboardTasksResponse>(dashboardUrl(endpoints.dashboard.tasks(), filters)),
  ]);

  return {
    summary: settledValue(summaryResult, undefined),
    activity: normalizeActivityItems(settledValue(activityResult, { items: [] })),
    findings: normalizeFindingCounts(settledValue(findingsResult, undefined)),
    tasks: normalizeTaskCounts(settledValue(tasksResult, undefined)),
    failures: {
      summary: summaryResult.status === "rejected",
      activity: activityResult.status === "rejected",
      findings: findingsResult.status === "rejected",
      tasks: tasksResult.status === "rejected",
    },
  };
}
