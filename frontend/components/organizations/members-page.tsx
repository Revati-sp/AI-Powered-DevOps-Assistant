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
import {
  countOwners,
  isSoleOwner,
  useAddMember,
  useMembers,
  useRemoveMember,
  useUpdateMember,
} from "@/features/organizations/hooks";
import {
  addMemberSchema,
  orgRoles,
  type AddMemberFormValues,
} from "@/features/organizations/schemas";
import type { OrganizationMemberResponse, OrgRole } from "@/features/organizations/types";
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
  const [addOpen, setAddOpen] = React.useState(false);
  const [pendingRole, setPendingRole] = React.useState<{
    member: OrganizationMemberResponse;
    role: OrgRole;
  } | null>(null);
  const [pendingRemove, setPendingRemove] = React.useState<OrganizationMemberResponse | null>(null);

  React.useEffect(() => {
    setOrganization(organizationId);
  }, [organizationId, setOrganization]);

  const { data, isLoading, isError, error, refetch } = useMembers(organizationId, {
    limit: PAGE_SIZE,
    offset: pageIndex * PAGE_SIZE,
  });
  const addMutation = useAddMember(organizationId);
  const updateMutation = useUpdateMember(organizationId);
  const removeMutation = useRemoveMember(organizationId);

  const members = data?.items ?? [];
  const ownerCount = countOwners(members);
  const canManage = role ? can(role, "member.manage") : false;

  const form = useForm<AddMemberFormValues>({
    resolver: zodResolver(addMemberSchema),
    defaultValues: { email: "", role: "member" },
  });

  React.useEffect(() => {
    if (addOpen) {
      form.reset({ email: "", role: "member" });
    }
  }, [addOpen, form]);

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

  const handleAdd = form.handleSubmit(async (values) => {
    try {
      await addMutation.mutateAsync(values);
      toast.success(`Added ${values.email}`);
      setAddOpen(false);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to add member");
    }
  });

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
            <Button type="button" onClick={() => setAddOpen(true)}>
              <UserPlus className="h-4 w-4" />
              Add member
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

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add member</DialogTitle>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={handleAdd} className="space-y-4">
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
                        disabled={addMutation.isPending}
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
                      disabled={addMutation.isPending}
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
                  disabled={addMutation.isPending}
                  onClick={() => setAddOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={addMutation.isPending}>
                  {addMutation.isPending ? "Adding…" : "Add member"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

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
