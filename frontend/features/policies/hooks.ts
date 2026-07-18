"use client";

import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from "@tanstack/react-query";

import { queryKeys } from "@/lib/api/query-keys";

import {
  createPolicyPack,
  createPolicyRule,
  deletePolicyPack,
  deletePolicyRule,
  getPolicyPack,
  listPolicyPacks,
  updatePolicyPack,
  updatePolicyRule,
  type ListPolicyPacksParams,
} from "./api";
import type {
  PolicyPackCreateRequest,
  PolicyPackDetailResponse,
  PolicyPacksPage,
  PolicyPackUpdateRequest,
  PolicyRuleCreateRequest,
  PolicyRuleUpdateRequest,
} from "./types";

export function usePolicyPacks(
  organizationId: string,
  params: ListPolicyPacksParams = {},
  options?: Omit<UseQueryOptions<PolicyPacksPage>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.policyPacks.list(organizationId, params),
    queryFn: () => listPolicyPacks(organizationId, params),
    enabled: Boolean(organizationId),
    ...options,
  });
}

export function usePolicyPack(
  organizationId: string,
  policyPackId: string,
  options?: Omit<UseQueryOptions<PolicyPackDetailResponse>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.policyPacks.detail(organizationId, policyPackId),
    queryFn: () => getPolicyPack(organizationId, policyPackId),
    enabled: Boolean(organizationId && policyPackId),
    ...options,
  });
}

export function useCreatePolicyPack(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: PolicyPackCreateRequest) => createPolicyPack(organizationId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.policyPacks.all(organizationId),
      });
    },
  });
}

export function useUpdatePolicyPack(organizationId: string, policyPackId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: PolicyPackUpdateRequest) =>
      updatePolicyPack(organizationId, policyPackId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.policyPacks.all(organizationId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.policyPacks.detail(organizationId, policyPackId),
      });
    },
  });
}

export function useDeletePolicyPack(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (policyPackId: string) => deletePolicyPack(organizationId, policyPackId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.policyPacks.all(organizationId),
      });
    },
  });
}

export function useCreatePolicyRule(organizationId: string, policyPackId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: PolicyRuleCreateRequest) =>
      createPolicyRule(organizationId, policyPackId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.policyPacks.detail(organizationId, policyPackId),
      });
    },
  });
}

export function useUpdatePolicyRule(organizationId: string, policyPackId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ruleId, body }: { ruleId: string; body: PolicyRuleUpdateRequest }) =>
      updatePolicyRule(organizationId, policyPackId, ruleId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.policyPacks.detail(organizationId, policyPackId),
      });
    },
  });
}

export function useDeletePolicyRule(organizationId: string, policyPackId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ruleId: string) => deletePolicyRule(organizationId, policyPackId, ruleId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.policyPacks.detail(organizationId, policyPackId),
      });
    },
  });
}
