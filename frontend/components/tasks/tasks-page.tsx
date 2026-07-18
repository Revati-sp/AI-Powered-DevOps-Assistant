"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { ListTodo } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { useOrgRole } from "@/components/app-shell/use-org-role";
import { DataTable } from "@/components/data-display/data-table";
import { FilterBar } from "@/components/data-display/filter-bar";
import { JsonViewer } from "@/components/data-display/json-viewer";
import { PageHeader } from "@/components/data-display/page-header";
import { StatusBadge } from "@/components/data-display/status-badge";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PermissionGate } from "@/components/permissions/permission-gate";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { isActiveTaskStatus } from "@/features/tasks/polling";
import { useCancelTask, useTask, useTasks } from "@/features/tasks/hooks";
import type { TaskStatus, TaskSummaryResponse } from "@/features/tasks/types";
import { isApiClientError } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/formatters/date";
import { useWorkspaceStore } from "@/store/workspace-store";

const PAGE_SIZE = 20;
const STATUSES: TaskStatus[] = ["queued", "running", "succeeded", "failed", "cancelled"];

export function TasksPageClient() {
  const role = useOrgRole();
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const [pageIndex, setPageIndex] = React.useState(0);
  const [status, setStatus] = React.useState<string>("all");
  const [taskType, setTaskType] = React.useState("");
  const [selectedTaskId, setSelectedTaskId] = React.useState<string | null>(null);
  const [cancelTaskId, setCancelTaskId] = React.useState<string | null>(null);

  const filters = {
    status: status === "all" ? null : status,
    task_type: taskType.trim() || null,
    organization_id: organizationId,
    limit: PAGE_SIZE,
    offset: pageIndex * PAGE_SIZE,
  };

  const { data, isLoading, isError, error, refetch } = useTasks(filters);
  const detailQuery = useTask(selectedTaskId ?? "", {
    enabled: Boolean(selectedTaskId),
  });
  const cancelMutation = useCancelTask();

  const columns = React.useMemo<ColumnDef<TaskSummaryResponse>[]>(
    () => [
      {
        accessorKey: "task_type",
        header: "Type",
        cell: ({ row }) => (
          <button
            type="button"
            className="text-primary text-left font-medium hover:underline"
            onClick={() => setSelectedTaskId(row.original.id)}
          >
            {row.original.task_type}
          </button>
        ),
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <StatusBadge status={row.original.status} />,
      },
      {
        accessorKey: "progress",
        header: "Progress",
        cell: ({ row }) => (
          <div className="flex min-w-28 items-center gap-2">
            <Progress value={row.original.progress} className="h-2" />
            <span className="text-muted-foreground text-xs">{row.original.progress}%</span>
          </div>
        ),
      },
      {
        accessorKey: "created_at",
        header: "Created",
        cell: ({ row }) => formatDateTime(row.original.created_at),
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => {
          if (!isActiveTaskStatus(row.original.status)) {
            return null;
          }
          return (
            <PermissionGate permission="task.cancel" role={role}>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setCancelTaskId(row.original.id)}
              >
                Cancel
              </Button>
            </PermissionGate>
          );
        },
      },
    ],
    [role],
  );

  const handleCancel = async () => {
    if (!cancelTaskId) {
      return;
    }
    try {
      await cancelMutation.mutateAsync(cancelTaskId);
      toast.success("Task cancelled");
      setCancelTaskId(null);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to cancel task");
    }
  };

  if (isLoading) {
    return <LoadingState label="Loading tasks…" />;
  }

  if (isError) {
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load tasks"}
        requestId={isApiClientError(error) ? error.requestId : undefined}
        onRetry={() => void refetch()}
      />
    );
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tasks"
        description="Async jobs with adaptive polling while queued or running."
      />

      <FilterBar>
        <div className="w-44 space-y-1">
          <label className="text-muted-foreground text-xs">Status</label>
          <Select
            value={status}
            onValueChange={(value) => {
              setStatus(value);
              setPageIndex(0);
            }}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {STATUSES.map((item) => (
                <SelectItem key={item} value={item}>
                  {item}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-56 space-y-1">
          <label className="text-muted-foreground text-xs">Task type</label>
          <Input
            value={taskType}
            onChange={(event) => {
              setTaskType(event.target.value);
              setPageIndex(0);
            }}
            placeholder="e.g. log_analysis"
          />
        </div>
      </FilterBar>

      {items.length === 0 ? (
        <EmptyState
          icon={<ListTodo />}
          title="No tasks"
          description="Async work will appear here when you run long-running operations."
        />
      ) : (
        <DataTable
          columns={columns}
          data={items}
          pagination={{
            pageIndex,
            pageSize: PAGE_SIZE,
            pageCount,
            totalRows: total,
            onPageChange: setPageIndex,
          }}
        />
      )}

      <Sheet
        open={Boolean(selectedTaskId)}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedTaskId(null);
          }
        }}
      >
        <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>Task details</SheetTitle>
          </SheetHeader>
          {detailQuery.isLoading ? (
            <LoadingState label="Loading task…" />
          ) : detailQuery.data ? (
            <div className="mt-4 space-y-4">
              <dl className="grid gap-3 text-sm">
                <div>
                  <dt className="text-muted-foreground">Type</dt>
                  <dd className="font-medium">{detailQuery.data.task_type}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Status</dt>
                  <dd>
                    <StatusBadge status={detailQuery.data.status} />
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Progress</dt>
                  <dd>{detailQuery.data.progress}%</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Created</dt>
                  <dd>{formatDateTime(detailQuery.data.created_at)}</dd>
                </div>
                {detailQuery.data.error_message ? (
                  <div>
                    <dt className="text-muted-foreground">Error</dt>
                    <dd className="text-destructive">{detailQuery.data.error_message}</dd>
                  </div>
                ) : null}
              </dl>
              {detailQuery.data.result_json ? (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">Result</h3>
                  <JsonViewer data={detailQuery.data.result_json} />
                </div>
              ) : null}
              {isActiveTaskStatus(detailQuery.data.status) ? (
                <PermissionGate permission="task.cancel" role={role}>
                  <Button
                    type="button"
                    variant="destructive"
                    onClick={() => setCancelTaskId(detailQuery.data!.id)}
                  >
                    Cancel task
                  </Button>
                </PermissionGate>
              ) : null}
            </div>
          ) : (
            <ErrorState message="Task not found." />
          )}
        </SheetContent>
      </Sheet>

      <ConfirmationDialog
        open={Boolean(cancelTaskId)}
        onOpenChange={(open) => {
          if (!open) {
            setCancelTaskId(null);
          }
        }}
        title="Cancel task?"
        description="The task will stop if it has not already completed."
        confirmLabel="Cancel task"
        variant="destructive"
        loading={cancelMutation.isPending}
        onConfirm={() => void handleCancel()}
      />
    </div>
  );
}
