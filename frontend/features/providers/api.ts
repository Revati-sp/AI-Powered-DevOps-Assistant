import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";

import type {
  ProviderConfigPatchRequest,
  ProviderConfigResponse,
  ProviderHealthResponse,
  ProviderRoutingPatchRequest,
  ProviderRoutingResponse,
} from "./types";

export function listAdminProviderConfigs(): Promise<ProviderConfigResponse[]> {
  return apiFetch<ProviderConfigResponse[]>(endpoints.admin.providers.configs());
}

export function patchAdminProviderConfig(
  providerName: string,
  body: ProviderConfigPatchRequest,
): Promise<ProviderConfigResponse> {
  return apiFetch<ProviderConfigResponse>(endpoints.admin.providers.config(providerName), {
    method: "PATCH",
    body,
  });
}

export function listAdminProviderRouting(): Promise<ProviderRoutingResponse[]> {
  return apiFetch<ProviderRoutingResponse[]>(endpoints.admin.providers.routing());
}

export function patchAdminProviderRouting(
  operation: string,
  body: ProviderRoutingPatchRequest,
): Promise<ProviderRoutingResponse> {
  return apiFetch<ProviderRoutingResponse>(
    endpoints.admin.providers.routingOperation(operation),
    { method: "PATCH", body },
  );
}

export function fetchAdminProviderHealth(): Promise<ProviderHealthResponse[]> {
  return apiFetch<ProviderHealthResponse[]>(endpoints.admin.providers.health());
}

export function listOrgProviderConfigs(organizationId: string): Promise<ProviderConfigResponse[]> {
  return apiFetch<ProviderConfigResponse[]>(endpoints.organizations.providers.configs(organizationId));
}

export function patchOrgProviderConfig(
  organizationId: string,
  providerName: string,
  body: ProviderConfigPatchRequest,
): Promise<ProviderConfigResponse> {
  return apiFetch<ProviderConfigResponse>(
    endpoints.organizations.providers.config(organizationId, providerName),
    { method: "PATCH", body },
  );
}

export function listOrgProviderRouting(
  organizationId: string,
): Promise<ProviderRoutingResponse[]> {
  return apiFetch<ProviderRoutingResponse[]>(
    endpoints.organizations.providers.routing(organizationId),
  );
}

export function patchOrgProviderRouting(
  organizationId: string,
  operation: string,
  body: ProviderRoutingPatchRequest,
): Promise<ProviderRoutingResponse> {
  return apiFetch<ProviderRoutingResponse>(
    endpoints.organizations.providers.routingOperation(organizationId, operation),
    { method: "PATCH", body },
  );
}
