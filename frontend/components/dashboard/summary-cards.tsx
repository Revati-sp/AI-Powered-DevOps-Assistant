import { Building2, FileCode2, ListTodo, MessageSquare } from "lucide-react";

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

  const totals = snapshot?.totals;
  const activeTasks =
    (snapshot?.taskStatusCounts.queued ?? 0) + (snapshot?.taskStatusCounts.running ?? 0);

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Conversations"
        value={totals?.conversations ?? "—"}
        description="Recent chats available in this workspace"
        icon={<MessageSquare />}
      />
      <StatCard
        label="Artifacts"
        value={totals?.artifacts ?? "—"}
        description="Generated configs and reviews"
        icon={<FileCode2 />}
      />
      <StatCard
        label="Tasks"
        value={totals?.tasks ?? "—"}
        description={
          activeTasks > 0 ? `${activeTasks} currently active` : "No active background jobs"
        }
        icon={<ListTodo />}
      />
      <StatCard
        label="Organizations"
        value={totals?.organizations ?? "—"}
        description="Workspaces you can access"
        icon={<Building2 />}
      />
    </div>
  );
}
