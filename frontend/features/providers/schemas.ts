import { z } from "zod";

import { LLM_OPERATIONS, PROVIDER_NAMES } from "./types";

export const providerConfigPatchSchema = z.object({
  enabled: z.boolean(),
  default_model: z.string().trim().min(1, "Model is required").max(120),
  timeout_seconds: z.number().int().min(1).max(600),
  max_retries: z.number().int().min(0).max(10),
  priority: z.number().int().min(0).max(1000),
  max_output_tokens: z.number().int().min(1).max(128000),
});

export type ProviderConfigPatchFormValues = z.infer<typeof providerConfigPatchSchema>;

export const providerRoutingPatchSchema = z.object({
  primary_provider: z.enum(PROVIDER_NAMES),
  fallback_providers: z.array(z.enum(PROVIDER_NAMES)),
});

export type ProviderRoutingPatchFormValues = z.infer<typeof providerRoutingPatchSchema>;

export const adminProviderConfigPatchSchema = providerConfigPatchSchema.extend({
  secret_env_key: z.string().trim().max(120).optional().or(z.literal("")),
  base_url_env_key: z.string().trim().max(120).optional().or(z.literal("")),
  model_env_key: z.string().trim().max(120).optional().or(z.literal("")),
});

export type AdminProviderConfigPatchFormValues = z.infer<typeof adminProviderConfigPatchSchema>;

export const operationEnum = z.enum(LLM_OPERATIONS);
