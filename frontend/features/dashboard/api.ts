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
    apiFetch<DashboardActivityItem[]>(dashboardUrl(endpoints.dashboard.activity(), filters)),
    apiFetch<DashboardSummary["findings"]>(dashboardUrl(endpoints.dashboard.findings(), filters)),
    apiFetch<DashboardTaskCounts>(dashboardUrl(endpoints.dashboard.tasks(), filters)),
  ]);

  return {
    summary: settledValue(summaryResult, undefined),
    activity: settledValue(activityResult, []),
    findings: settledValue(findingsResult, undefined),
    tasks: settledValue(tasksResult, undefined),
    failures: {
      summary: summaryResult.status === "rejected",
      activity: activityResult.status === "rejected",
      findings: findingsResult.status === "rejected",
      tasks: tasksResult.status === "rejected",
    },
  };
}
