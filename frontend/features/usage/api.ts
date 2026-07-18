import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";

import type {
  OrganizationQuotaPatchRequest,
  OrganizationQuotaResponse,
  OrganizationUsageResponse,
  UserUsageResponse,
} from "./types";

export function fetchMyUsage(): Promise<UserUsageResponse> {
  return apiFetch<UserUsageResponse>(endpoints.usage.me());
}

export function fetchOrganizationUsage(organizationId: string): Promise<OrganizationUsageResponse> {
  return apiFetch<OrganizationUsageResponse>(endpoints.organizations.usage(organizationId));
}

export function fetchOrganizationQuotas(
  organizationId: string,
): Promise<OrganizationQuotaResponse | null> {
  return apiFetch<OrganizationQuotaResponse | null>(endpoints.organizations.quotas(organizationId));
}

export function patchOrganizationQuotas(
  organizationId: string,
  body: OrganizationQuotaPatchRequest,
): Promise<OrganizationQuotaResponse> {
  return apiFetch<OrganizationQuotaResponse>(endpoints.organizations.quotas(organizationId), {
    method: "PATCH",
    body,
  });
}
