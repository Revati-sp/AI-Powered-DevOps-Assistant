import type { components } from "@/lib/api/generated-types";

export type LogAnalyzeRequest = components["schemas"]["LogAnalyzeRequest"];
export type LogAnalyzeResult = components["schemas"]["LogAnalyzeResult"];
export type AsyncTaskResponse = components["schemas"]["AsyncTaskResponse"];
export type TaskDetailResponse = components["schemas"]["TaskDetailResponse"];
export type TaskStatus = components["schemas"]["TaskStatus"];
export type LogSeverity = LogAnalyzeResult["severity"];
