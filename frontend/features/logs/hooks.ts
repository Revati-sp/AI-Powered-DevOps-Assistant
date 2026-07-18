"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  analyzeLogs,
  analyzeLogsAsync,
  analyzeLogsUpload,
  fetchTaskDetail,
} from "@/features/logs/api";
import { taskPollInterval } from "@/features/logs/task-utils";
import type { LogAnalyzeRequest } from "@/features/logs/types";
import { queryKeys } from "@/lib/api/query-keys";

export { isTaskActive, parseTaskLogResult, taskPollInterval } from "@/features/logs/task-utils";

export function useAnalyzeLogsMutation() {
  return useMutation({
    mutationFn: (body: LogAnalyzeRequest) => analyzeLogs(body),
  });
}

export function useAnalyzeLogsUploadMutation() {
  return useMutation({
    mutationFn: ({ file, provider }: { file: File; provider: string }) =>
      analyzeLogsUpload(file, provider),
  });
}

export function useAnalyzeLogsAsyncMutation() {
  return useMutation({
    mutationFn: ({
      content,
      provider,
      organizationId,
      idempotencyKey,
    }: {
      content: string;
      provider: string;
      organizationId?: string | null;
      idempotencyKey?: string;
    }) =>
      analyzeLogsAsync(
        {
          content,
          provider,
          organization_id: organizationId ?? null,
        },
        { idempotencyKey },
      ),
  });
}

export function useLogAnalysisTask(taskId: string | null) {
  return useQuery({
    queryKey: taskId ? queryKeys.tasks.detail(taskId) : queryKeys.tasks.detail("none"),
    queryFn: () => fetchTaskDetail(taskId as string),
    enabled: Boolean(taskId),
    refetchInterval: (query) => taskPollInterval(query.state.data?.status),
  });
}

/** Drop in-flight async log task caches when switching workspace organization. */
export function useClearLogTaskCacheOnOrgChange(organizationId: string | null) {
  const queryClient = useQueryClient();
  return () => {
    void queryClient.removeQueries({ queryKey: queryKeys.tasks.all() });
    void organizationId;
  };
}
