export const LLM_OPERATIONS = [
  "chat",
  "log_analysis",
  "configuration_review",
  "dockerfile_generation",
  "kubernetes",
] as const;

export type LLMOperation = (typeof LLM_OPERATIONS)[number];

export const PROVIDER_NAMES = ["gemini", "llama", "mistral"] as const;

export type ProviderName = (typeof PROVIDER_NAMES)[number];

export type ProviderConfigResponse = {
  id: string;
  organization_id: string | null;
  provider_name: string;
  enabled: boolean;
  default_model: string;
  timeout_seconds: number;
  max_retries: number;
  priority: number;
  max_output_tokens: number;
  secret_env_key: string;
  base_url_env_key: string | null;
  model_env_key: string | null;
  configured: boolean;
  created_at: string;
  updated_at: string;
};

export type ProviderConfigPatchRequest = {
  enabled?: boolean;
  default_model?: string;
  timeout_seconds?: number;
  max_retries?: number;
  priority?: number;
  max_output_tokens?: number;
  secret_env_key?: string;
  base_url_env_key?: string | null;
  model_env_key?: string | null;
};

export type ProviderRoutingResponse = {
  id: string;
  organization_id: string | null;
  operation: LLMOperation;
  primary_provider: string;
  fallback_providers: string[];
  created_at: string;
  updated_at: string;
};

export type ProviderRoutingPatchRequest = {
  primary_provider?: string;
  fallback_providers?: string[];
};

export type ProviderHealthResponse = {
  provider_name: string;
  enabled: boolean;
  configured: boolean;
  last_failure_category: string | null;
  circuit_state: string;
  avg_latency_ms: number | null;
};
