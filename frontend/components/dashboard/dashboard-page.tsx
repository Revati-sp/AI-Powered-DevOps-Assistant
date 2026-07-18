"use client";

import { useQuery } from "@tanstack/react-query";

import { FindingsOverview } from "@/components/dashboard/findings-overview";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { RecentActivity } from "@/components/dashboard/recent-activity";
import { SummaryCards } from "@/components/dashboard/summary-cards";
import { TaskStatusChart } from "@/components/dashboard/task-status-chart";
import { WorkspaceStatus } from "@/components/dashboard/workspace-status";
import { WelcomeBanner } from "@/components/onboarding/welcome-banner";
import { PageHeader } from "@/components/data-display/page-header";
import { ErrorState } from "@/components/feedback/error-state";
import { fetchDashboardSnapshot } from "@/features/dashboard/api";

const DASHBOARD_QUERY_KEY = ["dashboard", "snapshot"] as const;

const EMPTY_COUNTS = {
  queued: 0,
  running: 0,
  succeeded: 0,
  failed: 0,
  cancelled: 0,
};

export function DashboardPage() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: DASHBOARD_QUERY_KEY,
    queryFn: fetchDashboardSnapshot,
    staleTime: 30_000,
  });

  const allFailed =
    isError ||
    (data &&
      data.failures.conversations &&
      data.failures.artifacts &&
      data.failures.tasks &&
      data.failures.organizations);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Overview of recent activity, running tasks, and workspace health."
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
                items={data?.recentActivity ?? []}
                loading={isLoading || isFetching}
              />
            </div>
            <WorkspaceStatus snapshot={data} loading={isLoading} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <TaskStatusChart counts={data?.taskStatusCounts ?? EMPTY_COUNTS} loading={isLoading} />
            <FindingsOverview />
          </div>

          <QuickActions />
        </>
      )}
    </div>
  );
}
