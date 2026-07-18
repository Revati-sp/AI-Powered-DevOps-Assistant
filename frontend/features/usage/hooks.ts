"use client";

import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from "@tanstack/react-query";

import { queryKeys } from "@/lib/api/query-keys";

import {
  fetchMyUsage,
  fetchOrganizationQuotas,
  fetchOrganizationUsage,
  patchOrganizationQuotas,
} from "./api";
import type {
  OrganizationQuotaPatchRequest,
  OrganizationQuotaResponse,
  OrganizationUsageResponse,
  UserUsageResponse,
} from "./types";

export function useMyUsage(
  options?: Omit<UseQueryOptions<UserUsageResponse>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.usage.me(),
    queryFn: fetchMyUsage,
    ...options,
  });
}

export function useOrganizationUsage(
  organizationId: string | null,
  options?: Omit<UseQueryOptions<OrganizationUsageResponse>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.usage.org(organizationId ?? "none"),
    queryFn: () => fetchOrganizationUsage(organizationId as string),
    enabled: Boolean(organizationId),
    ...options,
  });
}

export function useOrganizationQuotas(
  organizationId: string | null,
  options?: Omit<UseQueryOptions<OrganizationQuotaResponse | null>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.usage.quotas(organizationId ?? "none"),
    queryFn: () => fetchOrganizationQuotas(organizationId as string),
    enabled: Boolean(organizationId),
    ...options,
  });
}

export function usePatchOrganizationQuotas(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: OrganizationQuotaPatchRequest) =>
      patchOrganizationQuotas(organizationId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.usage.org(organizationId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.usage.quotas(organizationId) });
    },
  });
}
