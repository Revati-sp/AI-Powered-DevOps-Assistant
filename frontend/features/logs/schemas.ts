import { z } from "zod";

import { LLM_PROVIDERS } from "@/lib/constants/app";

export const LOG_CONTENT_MIN = 1;
export const LOG_CONTENT_MAX = 500_000;
/** Prefer async analysis above this size to avoid long request timeouts. */
export const LOG_ASYNC_THRESHOLD = 80_000;

export const providerSchema = z.enum(LLM_PROVIDERS);

export const logWorkspaceSchema = z.enum(["personal", "organization"]);

export const logAnalyzePasteSchema = z.object({
  content: z
    .string()
    .min(LOG_CONTENT_MIN, "Log content is required")
    .max(LOG_CONTENT_MAX, `Log content must be at most ${LOG_CONTENT_MAX} characters`),
  provider: providerSchema,
  async_mode: z.boolean(),
  workspace: logWorkspaceSchema,
});

export type LogAnalyzePasteValues = z.infer<typeof logAnalyzePasteSchema>;

export const logAnalyzeResultSchema = z.object({
  summary: z.string(),
  severity: z.enum(["low", "medium", "high", "critical"]),
  detected_errors: z.array(z.string()).optional().default([]),
  possible_causes: z.array(z.string()).optional().default([]),
  recommended_actions: z.array(z.string()).optional().default([]),
  diagnostic_commands: z.array(z.string()).optional().default([]),
  confidence: z.number(),
  disclaimer: z.string(),
});

export type ParsedLogAnalyzeResult = z.infer<typeof logAnalyzeResultSchema>;
