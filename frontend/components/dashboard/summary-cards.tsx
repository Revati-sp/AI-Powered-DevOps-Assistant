import { FileCode2, ListTodo, MessageSquare, ShieldAlert } from "lucide-react";

import { StatCard } from "@/components/data-display/stat-card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  normalizeFindingCounts,
  normalizeTaskCounts,
  type DashboardSnapshot,
} from "@/features/dashboard/api";

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

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
  const tasks = normalizeTaskCounts(summary?.tasks);
  const findings = normalizeFindingCounts(summary?.findings);
  const activeTasks = asNumber(tasks?.queued) + asNumber(tasks?.running);
  const taskTotal =
    asNumber(tasks?.queued) +
    asNumber(tasks?.running) +
    asNumber(tasks?.succeeded) +
    asNumber(tasks?.failed);
  const findingsTotal = asNumber(findings?.critical) + asNumber(findings?.high);

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Conversations"
        value={summary ? asNumber(summary.conversations?.total) : "—"}
        description={`${asNumber(summary?.conversations?.recent)} recent in selected period`}
        icon={<MessageSquare />}
      />
      <StatCard
        label="Artifacts"
        value={summary ? asNumber(summary.artifacts?.total) : "—"}
        description={`${asNumber(summary?.artifacts?.favorites)} favorites · ${asNumber(summary?.artifacts?.archived)} archived`}
        icon={<FileCode2 />}
      />
      <StatCard
        label="Tasks"
        value={summary && tasks ? taskTotal : "—"}
        description={
          activeTasks > 0 ? `${activeTasks} currently active` : "No active background jobs"
        }
        icon={<ListTodo />}
      />
      <StatCard
        label="Findings"
        value={summary && findings ? findingsTotal : "—"}
        description={`${asNumber(findings?.critical)} critical · ${asNumber(findings?.high)} high`}
        icon={<ShieldAlert />}
      />
    </div>
  );
}
