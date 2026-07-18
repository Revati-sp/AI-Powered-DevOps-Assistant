"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { components } from "@/lib/api/generated-types";
import { queryKeys } from "@/lib/api/query-keys";
import type { OrgRole } from "@/lib/permissions/rbac";
import { useAuth } from "@/providers/auth-provider";
import { useWorkspaceStore } from "@/store/workspace-store";

type MembersPage = components["schemas"]["Page_OrganizationMemberResponse_"];

/**
 * Resolves the current user's org role for a specific organization.
 * Used for UX-only nav/permission gating; backend remains authoritative.
 */
export function useOrganizationRole(organizationId: string | null | undefined): OrgRole | null {
  const { user } = useAuth();

  const { data } = useQuery({
    queryKey: queryKeys.members.list(organizationId ?? "none"),
    queryFn: () => apiFetch<MembersPage>(endpoints.organizations.members(organizationId as string)),
    enabled: Boolean(organizationId && user?.id),
  });

  if (!organizationId || !user?.id || !data?.items) {
    return null;
  }

  return data.items.find((member) => member.user_id === user.id)?.role ?? null;
}

/**
 * Resolves the current user's org role for the selected workspace organization.
 */
export function useOrgRole(): OrgRole | null {
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  return useOrganizationRole(organizationId);
}
