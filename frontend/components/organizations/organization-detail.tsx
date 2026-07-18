"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { OrganizationFormDialog } from "@/components/organizations/organization-form-dialog";
import { PageHeader } from "@/components/data-display/page-header";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PermissionDenied } from "@/components/feedback/permission-denied";
import { PermissionGate } from "@/components/permissions/permission-gate";
import { useOrganizationRole } from "@/components/app-shell/use-org-role";
import { Button } from "@/components/ui/button";
import {
  useDeleteOrganization,
  useOrganization,
  useUpdateOrganization,
} from "@/features/organizations/hooks";
import type { OrganizationFormValues } from "@/features/organizations/schemas";
import { isApiClientError } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/formatters/date";
import { can } from "@/lib/permissions/rbac";
import { useWorkspaceStore } from "@/store/workspace-store";

type OrganizationDetailProps = {
  organizationId: string;
};

export function OrganizationDetail({ organizationId }: OrganizationDetailProps) {
  const router = useRouter();
  const role = useOrganizationRole(organizationId);
  const setOrganization = useWorkspaceStore((s) => s.setOrganization);
  const [editOpen, setEditOpen] = React.useState(false);
  const [deleteOpen, setDeleteOpen] = React.useState(false);

  React.useEffect(() => {
    setOrganization(organizationId);
  }, [organizationId, setOrganization]);

  const { data, isLoading, isError, error, refetch } = useOrganization(organizationId);
  const updateMutation = useUpdateOrganization(organizationId);
  const deleteMutation = useDeleteOrganization();

  const handleUpdate = async (values: OrganizationFormValues) => {
    try {
      await updateMutation.mutateAsync({
        name: values.name,
        slug: values.slug || undefined,
      });
      toast.success("Organization updated");
      setEditOpen(false);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to update organization");
    }
  };

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(organizationId);
      toast.success("Organization deleted");
      setOrganization(null);
      setDeleteOpen(false);
      router.push("/organizations");
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to delete organization");
    }
  };

  if (isLoading) {
    return <LoadingState label="Loading organization…" />;
  }

  if (isError || !data) {
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load organization"}
        requestId={isApiClientError(error) ? error.requestId : undefined}
        onRetry={() => void refetch()}
      />
    );
  }

  if (role && !can(role, "organization.read")) {
    return <PermissionDenied />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={data.name}
        description={`Slug: ${data.slug}`}
        actions={
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline">
              <Link href={`/organizations/${organizationId}/members`}>Members</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href={`/organizations/${organizationId}/policies`}>Policies</Link>
            </Button>
            <PermissionGate permission="audit.read" role={role}>
              <Button asChild variant="outline">
                <Link href={`/organizations/${organizationId}/audit`}>Audit</Link>
              </Button>
            </PermissionGate>
            <PermissionGate permission="organization.update" role={role}>
              <Button type="button" onClick={() => setEditOpen(true)}>
                Edit
              </Button>
            </PermissionGate>
            <PermissionGate permission="organization.delete" role={role}>
              <Button type="button" variant="destructive" onClick={() => setDeleteOpen(true)}>
                Delete
              </Button>
            </PermissionGate>
          </div>
        }
      />

      <dl className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1">
          <dt className="text-muted-foreground text-sm">Created</dt>
          <dd className="text-sm font-medium">{formatDateTime(data.created_at)}</dd>
        </div>
        <div className="space-y-1">
          <dt className="text-muted-foreground text-sm">Updated</dt>
          <dd className="text-sm font-medium">{formatDateTime(data.updated_at)}</dd>
        </div>
      </dl>

      <OrganizationFormDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        title="Edit organization"
        initial={data}
        loading={updateMutation.isPending}
        onSubmit={handleUpdate}
      />

      <ConfirmationDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete organization?"
        description="This permanently deletes the organization and cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
        loading={deleteMutation.isPending}
        onConfirm={() => void handleDelete()}
      />
    </div>
  );
}
