export type UsagePeriodSummary = {
  tokens: number;
  requests: number;
  estimated: boolean;
};

export type UsageEventResponse = {
  id: string;
  user_id: string;
  organization_id: string | null;
  operation: string;
  provider: string;
  model: string | null;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  is_estimated: boolean;
  created_at: string;
};

export type UserUsageResponse = {
  user_id: string;
  daily: UsagePeriodSummary;
  monthly: UsagePeriodSummary;
  recent_events: UsageEventResponse[];
};

export type OrganizationQuotaResponse = {
  id: string;
  organization_id: string;
  daily_token_limit: number | null;
  daily_request_limit: number | null;
  monthly_token_limit: number | null;
  monthly_request_limit: number | null;
  enforce_quotas: boolean;
  created_at: string;
  updated_at: string;
};

export type OrganizationUsageResponse = {
  organization_id: string;
  daily: UsagePeriodSummary;
  monthly: UsagePeriodSummary;
  quota: OrganizationQuotaResponse | null;
};

export type OrganizationQuotaPatchRequest = {
  daily_token_limit?: number | null;
  daily_request_limit?: number | null;
  monthly_token_limit?: number | null;
  monthly_request_limit?: number | null;
  enforce_quotas?: boolean;
  clear_daily_limits?: boolean;
  clear_monthly_limits?: boolean;
};

export type UsageLimitStatus = "ok" | "warning" | "over";
