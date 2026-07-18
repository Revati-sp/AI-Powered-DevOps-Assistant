import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { buildQueryString } from "@/lib/api/query-string";

import type { TaskCancelResponse, TaskDetailResponse, TasksPage } from "./types";

export type ListTasksParams = {
  status?: string | null;
  task_type?: string | null;
  organization_id?: string | null;
  limit?: number;
  offset?: number;
};

export function listTasks(params: ListTasksParams = {}): Promise<TasksPage> {
  const qs = buildQueryString({
    status: params.status ?? undefined,
    task_type: params.task_type ?? undefined,
    organization_id: params.organization_id ?? undefined,
    limit: params.limit ?? 20,
    offset: params.offset ?? 0,
  });
  return apiFetch<TasksPage>(`${endpoints.tasks.list()}${qs}`);
}

export function getTask(taskId: string): Promise<TaskDetailResponse> {
  return apiFetch<TaskDetailResponse>(endpoints.tasks.detail(taskId));
}

export function cancelTask(taskId: string): Promise<TaskCancelResponse> {
  return apiFetch<TaskCancelResponse>(endpoints.tasks.cancel(taskId), {
    method: "POST",
  });
}
