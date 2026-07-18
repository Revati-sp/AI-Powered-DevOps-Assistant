import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";

import type {
  AsyncTaskResponse,
  LogAnalyzeRequest,
  LogAnalyzeResult,
  TaskDetailResponse,
} from "@/features/logs/types";

export function analyzeLogs(body: LogAnalyzeRequest) {
  return apiFetch<LogAnalyzeResult>(endpoints.logs.analyze(), {
    method: "POST",
    body: {
      content: body.content,
      provider: body.provider,
      async_mode: false,
    },
    timeoutMs: 120_000,
  });
}

export function analyzeLogsUpload(file: File, provider: string) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("provider", provider);
  return apiFetch<LogAnalyzeResult>(endpoints.logs.analyzeUpload(), {
    method: "POST",
    formData,
    timeoutMs: 120_000,
  });
}

export function analyzeLogsAsync(
  body: Pick<LogAnalyzeRequest, "content" | "provider">,
  options?: { idempotencyKey?: string },
) {
  const headers: Record<string, string> = {};
  if (options?.idempotencyKey) {
    headers["Idempotency-Key"] = options.idempotencyKey;
  }
  return apiFetch<AsyncTaskResponse>(endpoints.logs.analyzeAsync(), {
    method: "POST",
    body: {
      content: body.content,
      provider: body.provider,
      async_mode: true,
    },
    headers,
    timeoutMs: 60_000,
  });
}

export function fetchTaskDetail(taskId: string) {
  return apiFetch<TaskDetailResponse>(endpoints.tasks.detail(taskId), {
    timeoutMs: 30_000,
  });
}
