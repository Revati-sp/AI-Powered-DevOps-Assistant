"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { FindingsOverview } from "@/components/dashboard/findings-overview";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { RecentActivity } from "@/components/dashboard/recent-activity";
import { SummaryCards } from "@/components/dashboard/summary-cards";
import { TaskStatusChart } from "@/components/dashboard/task-status-chart";
import { UsageProgress } from "@/components/dashboard/usage-progress";
import { WorkspaceStatus } from "@/components/dashboard/workspace-status";
import { WelcomeBanner } from "@/components/onboarding/welcome-banner";
import { PageHeader } from "@/components/data-display/page-header";
import { ErrorState } from "@/components/feedback/error-state";
import {
  fetchDashboardSnapshot,
  normalizeActivityItems,
  normalizeFindingCounts,
  normalizeTaskCounts,
} from "@/features/dashboard/api";
import { queryKeys } from "@/lib/api/query-keys";
import { useWorkspaceStore } from "@/store/workspace-store";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const EMPTY_COUNTS = {
  queued: 0,
  running: 0,
  succeeded: 0,
  failed: 0,
};

export function DashboardPage() {
  const organizationId = useWorkspaceStore((state) => state.currentOrganizationId);
  const [timeRange, setTimeRange] = useState<"24h" | "7d" | "30d">("7d");
  const filters = { organization_id: organizationId, time_range: timeRange };
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: queryKeys.dashboard.snapshot(filters),
    queryFn: () => fetchDashboardSnapshot(filters),
    staleTime: 30_000,
  });

  const allFailed =
    isError ||
    (data &&
      data.failures.summary &&
      data.failures.activity &&
      data.failures.tasks &&
      data.failures.findings);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Overview of recent activity, running tasks, and workspace health."
        actions={
          <Select value={timeRange} onValueChange={(value: "24h" | "7d" | "30d") => setTimeRange(value)}>
            <SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
        }
      />

      {allFailed ? (
        <ErrorState
          message="Could not load dashboard data. Check your connection and try again."
          onRetry={() => refetch()}
        />
      ) : (
        <>
          <WelcomeBanner />
          <SummaryCards snapshot={data} loading={isLoading} />

          <div className="grid gap-4 xl:grid-cols-3">
            <div className="xl:col-span-2">
              <RecentActivity
                items={normalizeActivityItems(data?.activity)}
                loading={isLoading || isFetching}
              />
            </div>
            <WorkspaceStatus snapshot={data} loading={isLoading} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <TaskStatusChart
              counts={normalizeTaskCounts(data?.tasks) ?? EMPTY_COUNTS}
              loading={isLoading}
            />
            <FindingsOverview counts={normalizeFindingCounts(data?.findings)} loading={isLoading} />
          </div>

          <UsageProgress snapshot={data} loading={isLoading} />
          <QuickActions />
        </>
      )}
    </div>
  );
}
