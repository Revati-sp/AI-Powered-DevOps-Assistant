"use client";

import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from "@tanstack/react-query";

import { queryKeys } from "@/lib/api/query-keys";

import {
  addMember,
  createOrganization,
  deleteOrganization,
  getOrganization,
  listMembers,
  listOrganizations,
  removeMember,
  updateMember,
  updateOrganization,
  type ListMembersParams,
  type ListOrganizationsParams,
} from "./api";
import type {
  AddMemberRequest,
  MembersPage,
  OrganizationCreate,
  OrganizationResponse,
  OrganizationsPage,
  OrganizationUpdate,
  UpdateMemberRequest,
} from "./types";

export function useOrganizations(
  params: ListOrganizationsParams = {},
  options?: Omit<UseQueryOptions<OrganizationsPage>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.organizations.list(params),
    queryFn: () => listOrganizations(params),
    ...options,
  });
}

export function useOrganization(
  organizationId: string,
  options?: Omit<UseQueryOptions<OrganizationResponse>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.organizations.detail(organizationId),
    queryFn: () => getOrganization(organizationId),
    enabled: Boolean(organizationId),
    ...options,
  });
}

export function useMembers(
  organizationId: string,
  params: ListMembersParams = {},
  options?: Omit<UseQueryOptions<MembersPage>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.members.list(organizationId, params),
    queryFn: () => listMembers(organizationId, params),
    enabled: Boolean(organizationId),
    ...options,
  });
}

export function useCreateOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: OrganizationCreate) => createOrganization(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.organizations.all(),
      });
    },
  });
}

export function useUpdateOrganization(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: OrganizationUpdate) => updateOrganization(organizationId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.organizations.all(),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.organizations.detail(organizationId),
      });
    },
  });
}

export function useDeleteOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (organizationId: string) => deleteOrganization(organizationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.organizations.all(),
      });
    },
  });
}

export function useAddMember(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: AddMemberRequest) => addMember(organizationId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.members.all(organizationId),
      });
    },
  });
}

export function useUpdateMember(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, body }: { userId: string; body: UpdateMemberRequest }) =>
      updateMember(organizationId, userId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.members.all(organizationId),
      });
    },
  });
}

export function useRemoveMember(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => removeMember(organizationId, userId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.members.all(organizationId),
      });
    },
  });
}

export function countOwners(members: { role: string }[] | undefined): number {
  return members?.filter((m) => m.role === "owner").length ?? 0;
}

export function isSoleOwner(
  member: { role: string },
  members: { role: string }[] | undefined,
): boolean {
  return member.role === "owner" && countOwners(members) <= 1;
}
