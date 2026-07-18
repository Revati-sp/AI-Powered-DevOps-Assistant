"use client";

import dynamic from "next/dynamic";
import { ListTodo } from "lucide-react";

import { SectionHeader } from "@/components/data-display/section-header";
import { EmptyState } from "@/components/feedback/empty-state";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { TaskStatusCounts } from "@/features/dashboard/api";

const TaskStatusChartInner = dynamic(
  () =>
    import("@/components/dashboard/task-status-chart-inner").then(
      (mod) => mod.TaskStatusChartInner,
    ),
  {
    ssr: false,
    loading: () => <Skeleton className="h-56 w-full" />,
  },
);

export function TaskStatusChart({
  counts,
  loading,
}: {
  counts: TaskStatusCounts;
  loading?: boolean;
}) {
  const total = Object.values(counts).reduce((sum, value) => sum + value, 0);

  return (
    <Card className="h-full">
      <CardContent className="space-y-4 p-6">
        <SectionHeader title="Task status" description="Distribution from the latest 20 tasks" />

        {loading ? (
          <Skeleton className="h-56 w-full" />
        ) : total === 0 ? (
          <EmptyState
            className="py-8"
            icon={<ListTodo />}
            title="No tasks yet"
            description="Async jobs will appear here once you run log analysis or long-running work."
          />
        ) : (
          <TaskStatusChartInner counts={counts} />
        )}
      </CardContent>
    </Card>
  );
}
