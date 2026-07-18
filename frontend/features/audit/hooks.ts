"use client";

import { useQuery, type UseQueryOptions } from "@tanstack/react-query";

import { queryKeys } from "@/lib/api/query-keys";

import { listAuditEvents, type ListAuditEventsParams } from "./api";
import type { AuditEventsPage } from "./types";

export function useAuditEvents(
  organizationId: string,
  params: ListAuditEventsParams = {},
  options?: Omit<UseQueryOptions<AuditEventsPage>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.auditEvents.list(organizationId, params),
    queryFn: () => listAuditEvents(organizationId, params),
    enabled: Boolean(organizationId),
    ...options,
  });
}
