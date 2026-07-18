import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { buildQueryString } from "@/lib/api/query-string";

import type { AuditEventsPage } from "./types";

export type ListAuditEventsParams = {
  action?: string | null;
  actor_user_id?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  created_from?: string | null;
  created_to?: string | null;
  limit?: number;
  offset?: number;
};

export function listAuditEvents(
  organizationId: string,
  params: ListAuditEventsParams = {},
): Promise<AuditEventsPage> {
  const qs = buildQueryString({
    action: params.action ?? undefined,
    actor_user_id: params.actor_user_id ?? undefined,
    resource_type: params.resource_type ?? undefined,
    resource_id: params.resource_id ?? undefined,
    created_from: params.created_from ?? undefined,
    created_to: params.created_to ?? undefined,
    limit: params.limit ?? 20,
    offset: params.offset ?? 0,
  });
  return apiFetch<AuditEventsPage>(`${endpoints.audit.events(organizationId)}${qs}`);
}
