import type { components } from "@/lib/api/generated-types";

export type LogAnalyzeResult = components["schemas"]["LogAnalyzeResult"];
export type TaskDetailResponse = components["schemas"]["TaskDetailResponse"];
export type TaskStatus = components["schemas"]["TaskStatus"];
export type LogSeverity = LogAnalyzeResult["severity"];

/** Local contract: includes optional organization scope for async analysis. */
export type LogAnalyzeRequest = {
  content: string;
  provider: string;
  async_mode?: boolean;
  organization_id?: string | null;
};

export type AsyncTaskResponse = {
  task_id: string;
  status: string;
  analysis_id?: string | null;
  celery_task_id?: string | null;
  organization_id?: string | null;
};
