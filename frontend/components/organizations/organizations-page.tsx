"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { Building2, Plus } from "lucide-react";
import Link from "next/link";
import * as React from "react";
import { toast } from "sonner";

import { OrganizationFormDialog } from "@/components/organizations/organization-form-dialog";
import { DataTable } from "@/components/data-display/data-table";
import { PageHeader } from "@/components/data-display/page-header";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { Button } from "@/components/ui/button";
import { useCreateOrganization, useOrganizations } from "@/features/organizations/hooks";
import type { OrganizationFormValues } from "@/features/organizations/schemas";
import type { OrganizationResponse } from "@/features/organizations/types";
import { isApiClientError } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/formatters/date";
import { useWorkspaceStore } from "@/store/workspace-store";

const PAGE_SIZE = 20;

export function OrganizationsPageClient() {
  const [pageIndex, setPageIndex] = React.useState(0);
  const [createOpen, setCreateOpen] = React.useState(false);
  const setOrganization = useWorkspaceStore((s) => s.setOrganization);

  const { data, isLoading, isError, error, refetch } = useOrganizations({
    limit: PAGE_SIZE,
    offset: pageIndex * PAGE_SIZE,
  });
  const createMutation = useCreateOrganization();

  const columns = React.useMemo<ColumnDef<OrganizationResponse>[]>(
    () => [
      {
        accessorKey: "name",
        header: "Name",
        cell: ({ row }) => (
          <Link
            href={`/organizations/${row.original.id}`}
            className="text-primary font-medium hover:underline"
            onClick={() => setOrganization(row.original.id)}
          >
            {row.original.name}
          </Link>
        ),
      },
      {
        accessorKey: "slug",
        header: "Slug",
        cell: ({ row }) => (
          <span className="text-muted-foreground font-mono text-sm">{row.original.slug}</span>
        ),
      },
      {
        accessorKey: "created_at",
        header: "Created",
        cell: ({ row }) => formatDateTime(row.original.created_at),
      },
    ],
    [setOrganization],
  );

  const handleCreate = async (values: OrganizationFormValues) => {
    try {
      const org = await createMutation.mutateAsync({
        name: values.name,
        slug: values.slug || undefined,
      });
      setOrganization(org.id);
      toast.success(`Created ${org.name}`);
      setCreateOpen(false);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to create organization");
    }
  };

  if (isLoading) {
    return <LoadingState label="Loading organizations…" />;
  }

  if (isError) {
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load organizations"}
        requestId={isApiClientError(error) ? error.requestId : undefined}
        onRetry={() => void refetch()}
      />
    );
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Organizations"
        description="Manage organizations, membership, and shared workspace context."
        actions={
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            Create organization
          </Button>
        }
      />

      {items.length === 0 ? (
        <EmptyState
          icon={<Building2 />}
          title="No organizations yet"
          description="Create an organization to collaborate on artifacts, policies, and audits."
          action={
            <Button type="button" onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              Create organization
            </Button>
          }
        />
      ) : (
        <DataTable
          columns={columns}
          data={items}
          emptyMessage="No organizations found."
          pagination={{
            pageIndex,
            pageSize: PAGE_SIZE,
            pageCount,
            totalRows: total,
            onPageChange: setPageIndex,
          }}
        />
      )}

      <OrganizationFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="Create organization"
        description="Choose a name and optional slug for the new organization."
        loading={createMutation.isPending}
        onSubmit={handleCreate}
      />
    </div>
  );
}
