"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { UserPlus } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { useOrganizationRole } from "@/components/app-shell/use-org-role";
import { DataTable } from "@/components/data-display/data-table";
import { PageHeader } from "@/components/data-display/page-header";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PermissionDenied } from "@/components/feedback/permission-denied";
import { PermissionGate } from "@/components/permissions/permission-gate";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { SectionHeader } from "@/components/data-display/section-header";
import {
  countOwners,
  isSoleOwner,
  useCreateInvitation,
  useInvitations,
  useMembers,
  useRemoveMember,
  useResendInvitation,
  useRevokeInvitation,
  useUpdateMember,
} from "@/features/organizations/hooks";
import {
  inviteMemberSchema,
  orgRoles,
  type InviteMemberFormValues,
} from "@/features/organizations/schemas";
import type {
  InvitationResponse,
  OrganizationMemberResponse,
  OrgRole,
} from "@/features/organizations/types";
import { isApiClientError } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/formatters/date";
import { can } from "@/lib/permissions/rbac";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useWorkspaceStore } from "@/store/workspace-store";

const PAGE_SIZE = 50;

type MembersPageProps = {
  organizationId: string;
};

export function MembersPageClient({ organizationId }: MembersPageProps) {
  const role = useOrganizationRole(organizationId);
  const setOrganization = useWorkspaceStore((s) => s.setOrganization);
  const [pageIndex, setPageIndex] = React.useState(0);
  const [inviteOpen, setInviteOpen] = React.useState(false);
  const [pendingRole, setPendingRole] = React.useState<{
    member: OrganizationMemberResponse;
    role: OrgRole;
  } | null>(null);
  const [pendingRemove, setPendingRemove] = React.useState<OrganizationMemberResponse | null>(null);
  const [pendingRevokeInvitation, setPendingRevokeInvitation] =
    React.useState<InvitationResponse | null>(null);

  React.useEffect(() => {
    setOrganization(organizationId);
  }, [organizationId, setOrganization]);

  const { data, isLoading, isError, error, refetch } = useMembers(organizationId, {
    limit: PAGE_SIZE,
    offset: pageIndex * PAGE_SIZE,
  });
  const {
    data: invitationsData,
    isLoading: invitationsLoading,
    isError: invitationsError,
    error: invitationsQueryError,
    refetch: refetchInvitations,
  } = useInvitations(organizationId, { limit: PAGE_SIZE, offset: 0 });
  const inviteMutation = useCreateInvitation(organizationId);
  const resendMutation = useResendInvitation(organizationId);
  const revokeInvitationMutation = useRevokeInvitation(organizationId);
  const updateMutation = useUpdateMember(organizationId);
  const removeMutation = useRemoveMember(organizationId);

  const members = data?.items ?? [];
  const pendingInvitations =
    invitationsData?.items.filter((invitation) => invitation.status === "pending") ?? [];
  const ownerCount = countOwners(members);
  const canManage = role ? can(role, "member.manage") : false;

  const form = useForm<InviteMemberFormValues>({
    resolver: zodResolver(inviteMemberSchema),
    defaultValues: { email: "", role: "member" },
  });

  React.useEffect(() => {
    if (inviteOpen) {
      form.reset({ email: "", role: "member" });
    }
  }, [inviteOpen, form]);

  const requestRoleChange = (member: OrganizationMemberResponse, nextRole: OrgRole) => {
    if (member.role === nextRole) {
      return;
    }
    if (isSoleOwner(member, members) && nextRole !== "owner") {
      toast.error("Cannot demote the final owner. Transfer ownership first.");
      return;
    }
    if (member.role === "owner" && nextRole !== "owner") {
      setPendingRole({ member, role: nextRole });
      return;
    }
    void applyRoleChange(member, nextRole);
  };

  const applyRoleChange = async (member: OrganizationMemberResponse, nextRole: OrgRole) => {
    try {
      await updateMutation.mutateAsync({
        userId: member.user_id,
        body: { role: nextRole },
      });
      toast.success(`Updated role for ${member.email}`);
      setPendingRole(null);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to update member");
    }
  };

  const requestRemove = (member: OrganizationMemberResponse) => {
    if (isSoleOwner(member, members)) {
      toast.error("Cannot remove the final owner. Transfer ownership first.");
      return;
    }
    setPendingRemove(member);
  };

  const confirmRemove = async () => {
    if (!pendingRemove) {
      return;
    }
    try {
      await removeMutation.mutateAsync(pendingRemove.user_id);
      toast.success(`Removed ${pendingRemove.email}`);
      setPendingRemove(null);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to remove member");
    }
  };

  const handleInvite = form.handleSubmit(async (values) => {
    try {
      await inviteMutation.mutateAsync(values);
      toast.success(`Invitation sent to ${values.email}`);
      setInviteOpen(false);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to send invitation");
    }
  });

  const handleResendInvitation = async (invitation: InvitationResponse) => {
    try {
      await resendMutation.mutateAsync(invitation.id);
      toast.success(`Invitation resent to ${invitation.email}`);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to resend invitation");
    }
  };

  const confirmRevokeInvitation = async () => {
    if (!pendingRevokeInvitation) {
      return;
    }
    try {
      await revokeInvitationMutation.mutateAsync(pendingRevokeInvitation.id);
      toast.success(`Revoked invitation for ${pendingRevokeInvitation.email}`);
      setPendingRevokeInvitation(null);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to revoke invitation");
    }
  };

  const columns = React.useMemo<ColumnDef<OrganizationMemberResponse>[]>(
    () => [
      {
        accessorKey: "email",
        header: "Email",
        cell: ({ row }) => (
          <div>
            <div className="font-medium">{row.original.email}</div>
            <div className="text-muted-foreground text-xs">{row.original.username}</div>
          </div>
        ),
      },
      {
        accessorKey: "role",
        header: "Role",
        cell: ({ row }) => {
          const member = row.original;
          const sole = isSoleOwner(member, members);
          if (!canManage) {
            return <span className="capitalize">{member.role}</span>;
          }
          return (
            <Select
              value={member.role}
              disabled={sole || updateMutation.isPending}
              onValueChange={(value) => requestRoleChange(member, value as OrgRole)}
            >
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {orgRoles.map((orgRole) => (
                  <SelectItem key={orgRole} value={orgRole}>
                    {orgRole}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          );
        },
      },
      {
        accessorKey: "updated_at",
        header: "Updated",
        cell: ({ row }) => formatDateTime(row.original.updated_at),
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => {
          if (!canManage) {
            return null;
          }
          const member = row.original;
          const sole = isSoleOwner(member, members);
          return (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={sole || removeMutation.isPending}
              onClick={() => requestRemove(member)}
            >
              Remove
            </Button>
          );
        },
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps -- handlers close over latest members
    [canManage, members, removeMutation.isPending, updateMutation.isPending],
  );

  if (isLoading) {
    return <LoadingState label="Loading members…" />;
  }

  if (isError) {
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load members"}
        requestId={isApiClientError(error) ? error.requestId : undefined}
        onRetry={() => void refetch()}
      />
    );
  }

  if (role && !can(role, "organization.read")) {
    return <PermissionDenied />;
  }

  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Members"
        description={
          ownerCount === 1
            ? "One owner is required. The final owner cannot be demoted or removed."
            : "Invite teammates and manage organization roles."
        }
        actions={
          <PermissionGate permission="member.manage" role={role}>
            <Button type="button" onClick={() => setInviteOpen(true)}>
              <UserPlus className="h-4 w-4" />
              Invite member
            </Button>
          </PermissionGate>
        }
      />

      <DataTable
        columns={columns}
        data={members}
        emptyMessage="No members found."
        pagination={{
          pageIndex,
          pageSize: PAGE_SIZE,
          pageCount,
          totalRows: total,
          onPageChange: setPageIndex,
        }}
      />

      <section className="space-y-4" aria-labelledby="pending-invitations-heading">
        <SectionHeader
          id="pending-invitations-heading"
          title="Pending invitations"
          description="Email invitations waiting to be accepted."
        />

        {invitationsLoading ? <LoadingState label="Loading invitations…" /> : null}

        {invitationsError ? (
          <ErrorState
            message={
              isApiClientError(invitationsQueryError)
                ? invitationsQueryError.message
                : "Failed to load invitations"
            }
            requestId={
              isApiClientError(invitationsQueryError)
                ? invitationsQueryError.requestId
                : undefined
            }
            onRetry={() => void refetchInvitations()}
          />
        ) : null}

        {!invitationsLoading && !invitationsError && pendingInvitations.length === 0 ? (
          <p className="text-muted-foreground text-sm">No pending invitations.</p>
        ) : null}

        {!invitationsLoading && !invitationsError && pendingInvitations.length > 0 ? (
          <ul className="divide-border divide-y rounded-md border">
            {pendingInvitations.map((invitation) => (
              <li
                key={invitation.id}
                className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium">{invitation.email}</span>
                    <Badge variant="outline" className="capitalize">
                      {invitation.role}
                    </Badge>
                    <Badge variant="warning">Pending</Badge>
                  </div>
                  <p className="text-muted-foreground text-xs">
                    Sent {formatDateTime(invitation.created_at)} · Expires{" "}
                    {formatDateTime(invitation.expires_at)}
                  </p>
                </div>
                {canManage ? (
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={resendMutation.isPending || revokeInvitationMutation.isPending}
                      onClick={() => void handleResendInvitation(invitation)}
                    >
                      Resend
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      disabled={resendMutation.isPending || revokeInvitationMutation.isPending}
                      onClick={() => setPendingRevokeInvitation(invitation)}
                    >
                      Revoke
                    </Button>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invite member</DialogTitle>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={handleInvite} className="space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        autoComplete="email"
                        disabled={inviteMutation.isPending}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="role"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Role</FormLabel>
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                      disabled={inviteMutation.isPending}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {orgRoles.map((orgRole) => (
                          <SelectItem key={orgRole} value={orgRole}>
                            {orgRole}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  disabled={inviteMutation.isPending}
                  onClick={() => setInviteOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={inviteMutation.isPending}>
                  {inviteMutation.isPending ? "Sending…" : "Send invitation"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <ConfirmationDialog
        open={Boolean(pendingRevokeInvitation)}
        onOpenChange={(open) => {
          if (!open) {
            setPendingRevokeInvitation(null);
          }
        }}
        title="Revoke invitation?"
        description={
          pendingRevokeInvitation
            ? `Revoke the pending invitation for ${pendingRevokeInvitation.email}?`
            : undefined
        }
        confirmLabel="Revoke"
        variant="destructive"
        loading={revokeInvitationMutation.isPending}
        onConfirm={() => void confirmRevokeInvitation()}
      />

      <ConfirmationDialog
        open={Boolean(pendingRole)}
        onOpenChange={(open) => {
          if (!open) {
            setPendingRole(null);
          }
        }}
        title="Demote owner?"
        description={
          pendingRole
            ? `Change ${pendingRole.member.email} from owner to ${pendingRole.role}? Ensure another owner remains.`
            : undefined
        }
        confirmLabel="Demote"
        variant="destructive"
        loading={updateMutation.isPending}
        onConfirm={() => {
          if (pendingRole) {
            void applyRoleChange(pendingRole.member, pendingRole.role);
          }
        }}
      />

      <ConfirmationDialog
        open={Boolean(pendingRemove)}
        onOpenChange={(open) => {
          if (!open) {
            setPendingRemove(null);
          }
        }}
        title="Remove member?"
        description={
          pendingRemove
            ? pendingRemove.role === "owner"
              ? `Remove owner ${pendingRemove.email}? This cannot be undone.`
              : `Remove ${pendingRemove.email} from this organization?`
            : undefined
        }
        confirmLabel="Remove"
        variant="destructive"
        loading={removeMutation.isPending}
        onConfirm={() => void confirmRemove()}
      />
    </div>
  );
}
