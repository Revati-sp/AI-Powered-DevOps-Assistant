import { FileCode2, ListTodo, MessageSquare, ShieldAlert } from "lucide-react";

import { StatCard } from "@/components/data-display/stat-card";
import { Skeleton } from "@/components/ui/skeleton";
import type { DashboardSnapshot } from "@/features/dashboard/api";

export function SummaryCards({
  snapshot,
  loading,
}: {
  snapshot?: DashboardSnapshot;
  loading?: boolean;
}) {
  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-28 w-full" />
        ))}
      </div>
    );
  }

  const summary = snapshot?.summary;
  const activeTasks =
    (summary?.tasks.queued ?? 0) + (summary?.tasks.running ?? 0);

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Conversations"
        value={summary?.conversations.total ?? "—"}
        description={`${summary?.conversations.recent ?? 0} recent in selected period`}
        icon={<MessageSquare />}
      />
      <StatCard
        label="Artifacts"
        value={summary?.artifacts.total ?? "—"}
        description={`${summary?.artifacts.favorites ?? 0} favorites · ${summary?.artifacts.archived ?? 0} archived`}
        icon={<FileCode2 />}
      />
      <StatCard
        label="Tasks"
        value={
          summary
            ? summary.tasks.queued + summary.tasks.running + summary.tasks.succeeded + summary.tasks.failed
            : "—"
        }
        description={
          activeTasks > 0 ? `${activeTasks} currently active` : "No active background jobs"
        }
        icon={<ListTodo />}
      />
      <StatCard
        label="Findings"
        value={summary ? summary.findings.critical + summary.findings.high : "—"}
        description={`${summary?.findings.critical ?? 0} critical · ${summary?.findings.high ?? 0} high`}
        icon={<ShieldAlert />}
      />
    </div>
  );
}
