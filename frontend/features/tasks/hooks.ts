"use client";

import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from "@tanstack/react-query";

import { queryKeys } from "@/lib/api/query-keys";

import { cancelTask, getTask, listTasks, type ListTasksParams } from "./api";
import { getTasksRefetchInterval } from "./polling";
import type { TaskDetailResponse, TasksPage } from "./types";

export function useTasks(
  params: ListTasksParams = {},
  options?: Omit<UseQueryOptions<TasksPage>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.tasks.list(params),
    queryFn: () => listTasks(params),
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      return getTasksRefetchInterval(items.map((item) => item.status));
    },
    ...options,
  });
}

export function useTask(
  taskId: string,
  options?: Omit<UseQueryOptions<TaskDetailResponse>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.tasks.detail(taskId),
    queryFn: () => getTask(taskId),
    enabled: Boolean(taskId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status ? getTasksRefetchInterval([status]) : false;
    },
    ...options,
  });
}

export function useCancelTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => cancelTask(taskId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all() });
    },
  });
}
