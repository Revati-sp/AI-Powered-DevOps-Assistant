import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { buildQueryString } from "@/lib/api/query-string";

import type {
  AddMemberRequest,
  CreateInvitationRequest,
  InvitationResponse,
  InvitationsPage,
  MembersPage,
  OrganizationCreate,
  OrganizationMemberResponse,
  OrganizationResponse,
  OrganizationsPage,
  OrganizationUpdate,
  UpdateMemberRequest,
} from "./types";

export type ListOrganizationsParams = {
  limit?: number;
  offset?: number;
};

export type ListMembersParams = {
  limit?: number;
  offset?: number;
};

export function listOrganizations(
  params: ListOrganizationsParams = {},
): Promise<OrganizationsPage> {
  const qs = buildQueryString({
    limit: params.limit ?? 20,
    offset: params.offset ?? 0,
  });
  return apiFetch<OrganizationsPage>(`${endpoints.organizations.list()}${qs}`);
}

export function getOrganization(organizationId: string): Promise<OrganizationResponse> {
  return apiFetch<OrganizationResponse>(endpoints.organizations.detail(organizationId));
}

export function createOrganization(body: OrganizationCreate): Promise<OrganizationResponse> {
  return apiFetch<OrganizationResponse>(endpoints.organizations.list(), {
    method: "POST",
    body,
  });
}

export function updateOrganization(
  organizationId: string,
  body: OrganizationUpdate,
): Promise<OrganizationResponse> {
  return apiFetch<OrganizationResponse>(endpoints.organizations.detail(organizationId), {
    method: "PATCH",
    body,
  });
}

export function deleteOrganization(organizationId: string): Promise<void> {
  return apiFetch<void>(endpoints.organizations.detail(organizationId), {
    method: "DELETE",
  });
}

export function listMembers(
  organizationId: string,
  params: ListMembersParams = {},
): Promise<MembersPage> {
  const qs = buildQueryString({
    limit: params.limit ?? 50,
    offset: params.offset ?? 0,
  });
  return apiFetch<MembersPage>(`${endpoints.organizations.members(organizationId)}${qs}`);
}

export function addMember(
  organizationId: string,
  body: AddMemberRequest,
): Promise<OrganizationMemberResponse> {
  return apiFetch<OrganizationMemberResponse>(endpoints.organizations.members(organizationId), {
    method: "POST",
    body,
  });
}

export function updateMember(
  organizationId: string,
  userId: string,
  body: UpdateMemberRequest,
): Promise<OrganizationMemberResponse> {
  return apiFetch<OrganizationMemberResponse>(
    endpoints.organizations.member(organizationId, userId),
    { method: "PATCH", body },
  );
}

export function removeMember(organizationId: string, userId: string): Promise<void> {
  return apiFetch<void>(endpoints.organizations.member(organizationId, userId), {
    method: "DELETE",
  });
}

export type ListInvitationsParams = {
  limit?: number;
  offset?: number;
};

export function listInvitations(
  organizationId: string,
  params: ListInvitationsParams = {},
): Promise<InvitationsPage> {
  const qs = buildQueryString({
    limit: params.limit ?? 50,
    offset: params.offset ?? 0,
  });
  return apiFetch<InvitationsPage>(
    `${endpoints.organizations.invitations(organizationId)}${qs}`,
  );
}

export function createInvitation(
  organizationId: string,
  body: CreateInvitationRequest,
): Promise<InvitationResponse> {
  return apiFetch<InvitationResponse>(endpoints.organizations.invitations(organizationId), {
    method: "POST",
    body,
  });
}

export function resendInvitation(
  organizationId: string,
  invitationId: string,
): Promise<InvitationResponse> {
  return apiFetch<InvitationResponse>(
    endpoints.organizations.resendInvitation(organizationId, invitationId),
    { method: "POST" },
  );
}

export function revokeInvitation(organizationId: string, invitationId: string): Promise<void> {
  return apiFetch<void>(endpoints.organizations.invitation(organizationId, invitationId), {
    method: "DELETE",
  });
}
