import { z } from "zod";

const limitField = z.number().int().min(0).nullable();

export const quotaFormSchema = z.object({
  daily_token_limit: limitField,
  daily_request_limit: limitField,
  monthly_token_limit: limitField,
  monthly_request_limit: limitField,
  enforce_quotas: z.boolean(),
  clear_daily_limits: z.boolean().optional(),
  clear_monthly_limits: z.boolean().optional(),
});

export type QuotaFormValues = z.infer<typeof quotaFormSchema>;

export function getUsageLimitStatus(
  used: number,
  limit: number | null | undefined,
): "ok" | "warning" | "over" {
  if (limit == null || limit <= 0) {
    return "ok";
  }
  const ratio = used / limit;
  if (ratio >= 1) {
    return "over";
  }
  if (ratio >= 0.8) {
    return "warning";
  }
  return "ok";
}
