"use client";

import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from "@tanstack/react-query";

import { queryKeys } from "@/lib/api/query-keys";

import {
  fetchAdminProviderHealth,
  listAdminProviderConfigs,
  listAdminProviderRouting,
  listOrgProviderConfigs,
  listOrgProviderRouting,
  patchAdminProviderConfig,
  patchAdminProviderRouting,
  patchOrgProviderConfig,
  patchOrgProviderRouting,
} from "./api";
import type {
  ProviderConfigPatchRequest,
  ProviderConfigResponse,
  ProviderHealthResponse,
  ProviderRoutingPatchRequest,
  ProviderRoutingResponse,
} from "./types";

export function useAdminProviderConfigs(
  options?: Omit<UseQueryOptions<ProviderConfigResponse[]>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.providers.adminConfigs(),
    queryFn: listAdminProviderConfigs,
    ...options,
  });
}

export function useAdminProviderRouting(
  options?: Omit<UseQueryOptions<ProviderRoutingResponse[]>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.providers.adminRouting(),
    queryFn: listAdminProviderRouting,
    ...options,
  });
}

export function useAdminProviderHealth(
  options?: Omit<UseQueryOptions<ProviderHealthResponse[]>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.providers.adminHealth(),
    queryFn: fetchAdminProviderHealth,
    ...options,
  });
}

export function usePatchAdminProviderConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      providerName,
      body,
    }: {
      providerName: string;
      body: ProviderConfigPatchRequest;
    }) => patchAdminProviderConfig(providerName, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.providers.adminConfigs() });
      void queryClient.invalidateQueries({ queryKey: queryKeys.providers.adminHealth() });
    },
  });
}

export function usePatchAdminProviderRouting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      operation,
      body,
    }: {
      operation: string;
      body: ProviderRoutingPatchRequest;
    }) => patchAdminProviderRouting(operation, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.providers.adminRouting() });
    },
  });
}

export function useOrgProviderConfigs(
  organizationId: string,
  options?: Omit<UseQueryOptions<ProviderConfigResponse[]>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.providers.orgConfigs(organizationId),
    queryFn: () => listOrgProviderConfigs(organizationId),
    enabled: Boolean(organizationId),
    ...options,
  });
}

export function useOrgProviderRouting(
  organizationId: string,
  options?: Omit<UseQueryOptions<ProviderRoutingResponse[]>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.providers.orgRouting(organizationId),
    queryFn: () => listOrgProviderRouting(organizationId),
    enabled: Boolean(organizationId),
    ...options,
  });
}

export function usePatchOrgProviderConfig(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      providerName,
      body,
    }: {
      providerName: string;
      body: ProviderConfigPatchRequest;
    }) => patchOrgProviderConfig(organizationId, providerName, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.providers.orgConfigs(organizationId),
      });
    },
  });
}

export function usePatchOrgProviderRouting(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      operation,
      body,
    }: {
      operation: string;
      body: ProviderRoutingPatchRequest;
    }) => patchOrgProviderRouting(organizationId, operation, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.providers.orgRouting(organizationId),
      });
    },
  });
}
