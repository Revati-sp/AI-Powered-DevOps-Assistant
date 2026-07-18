import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { buildQueryString } from "@/lib/api/query-string";

import type {
  PolicyPackCreateRequest,
  PolicyPackDetailResponse,
  PolicyPackResponse,
  PolicyPacksPage,
  PolicyPackUpdateRequest,
  PolicyRuleCreateRequest,
  PolicyRuleResponse,
  PolicyRuleUpdateRequest,
} from "./types";

export type ListPolicyPacksParams = {
  limit?: number;
  offset?: number;
};

export function listPolicyPacks(
  organizationId: string,
  params: ListPolicyPacksParams = {},
): Promise<PolicyPacksPage> {
  const qs = buildQueryString({
    limit: params.limit ?? 20,
    offset: params.offset ?? 0,
  });
  return apiFetch<PolicyPacksPage>(`${endpoints.policies.packs(organizationId)}${qs}`);
}

export function getPolicyPack(
  organizationId: string,
  policyPackId: string,
): Promise<PolicyPackDetailResponse> {
  return apiFetch<PolicyPackDetailResponse>(endpoints.policies.pack(organizationId, policyPackId));
}

export function createPolicyPack(
  organizationId: string,
  body: PolicyPackCreateRequest,
): Promise<PolicyPackResponse> {
  return apiFetch<PolicyPackResponse>(endpoints.policies.packs(organizationId), {
    method: "POST",
    body,
  });
}

export function updatePolicyPack(
  organizationId: string,
  policyPackId: string,
  body: PolicyPackUpdateRequest,
): Promise<PolicyPackResponse> {
  return apiFetch<PolicyPackResponse>(endpoints.policies.pack(organizationId, policyPackId), {
    method: "PATCH",
    body,
  });
}

export function deletePolicyPack(organizationId: string, policyPackId: string): Promise<void> {
  return apiFetch<void>(endpoints.policies.pack(organizationId, policyPackId), {
    method: "DELETE",
  });
}

export function createPolicyRule(
  organizationId: string,
  policyPackId: string,
  body: PolicyRuleCreateRequest,
): Promise<PolicyRuleResponse> {
  return apiFetch<PolicyRuleResponse>(endpoints.policies.rules(organizationId, policyPackId), {
    method: "POST",
    body,
  });
}

export function updatePolicyRule(
  organizationId: string,
  policyPackId: string,
  ruleId: string,
  body: PolicyRuleUpdateRequest,
): Promise<PolicyRuleResponse> {
  return apiFetch<PolicyRuleResponse>(
    endpoints.policies.rule(organizationId, policyPackId, ruleId),
    { method: "PATCH", body },
  );
}

export function deletePolicyRule(
  organizationId: string,
  policyPackId: string,
  ruleId: string,
): Promise<void> {
  return apiFetch<void>(endpoints.policies.rule(organizationId, policyPackId, ruleId), {
    method: "DELETE",
  });
}
