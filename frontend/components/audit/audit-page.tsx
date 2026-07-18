"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { ScrollText } from "lucide-react";
import * as React from "react";

import { useOrganizationRole } from "@/components/app-shell/use-org-role";
import { DataTable } from "@/components/data-display/data-table";
import { FilterBar } from "@/components/data-display/filter-bar";
import { JsonViewer } from "@/components/data-display/json-viewer";
import { PageHeader } from "@/components/data-display/page-header";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PermissionDenied } from "@/components/feedback/permission-denied";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useAuditEvents } from "@/features/audit/hooks";
import { labelRedactedMetadata } from "@/features/audit/redact";
import type { AuditEventResponse } from "@/features/audit/types";
import { isApiClientError } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/formatters/date";
import { can } from "@/lib/permissions/rbac";
import { useWorkspaceStore } from "@/store/workspace-store";

const PAGE_SIZE = 20;

type AuditPageProps = {
  organizationId: string;
};

export function AuditPageClient({ organizationId }: AuditPageProps) {
  const role = useOrganizationRole(organizationId);
  const setOrganization = useWorkspaceStore((s) => s.setOrganization);
  const [pageIndex, setPageIndex] = React.useState(0);
  const [action, setAction] = React.useState("");
  const [resourceType, setResourceType] = React.useState("");
  const [actorUserId, setActorUserId] = React.useState("");
  const [selected, setSelected] = React.useState<AuditEventResponse | null>(null);

  React.useEffect(() => {
    setOrganization(organizationId);
  }, [organizationId, setOrganization]);

  const canRead = role ? can(role, "audit.read") : false;

  const filters = {
    action: action.trim() || null,
    resource_type: resourceType.trim() || null,
    actor_user_id: actorUserId.trim() || null,
    limit: PAGE_SIZE,
    offset: pageIndex * PAGE_SIZE,
  };

  const { data, isLoading, isError, error, refetch } = useAuditEvents(organizationId, filters, {
    enabled: Boolean(organizationId) && canRead,
  });

  const columns = React.useMemo<ColumnDef<AuditEventResponse>[]>(
    () => [
      {
        accessorKey: "created_at",
        header: "When",
        cell: ({ row }) => formatDateTime(row.original.created_at),
      },
      {
        accessorKey: "action",
        header: "Action",
        cell: ({ row }) => (
          <button
            type="button"
            className="text-primary font-medium hover:underline"
            onClick={() => setSelected(row.original)}
          >
            {row.original.action}
          </button>
        ),
      },
      {
        accessorKey: "resource_type",
        header: "Resource",
        cell: ({ row }) => (
          <span>
            {row.original.resource_type}
            {row.original.resource_id ? (
              <span className="text-muted-foreground ml-1 font-mono text-xs">
                {row.original.resource_id.slice(0, 8)}
              </span>
            ) : null}
          </span>
        ),
      },
      {
        accessorKey: "actor_user_id",
        header: "Actor",
        cell: ({ row }) => (
          <span className="font-mono text-xs">
            {row.original.actor_user_id?.slice(0, 8) ?? "—"}
          </span>
        ),
      },
    ],
    [],
  );

  if (role === null) {
    return <LoadingState label="Checking permissions…" />;
  }

  if (!canRead) {
    return (
      <PermissionDenied
        title="Audit logs restricted"
        description="Only organization owners and admins can view audit events."
      />
    );
  }

  if (isLoading) {
    return <LoadingState label="Loading audit events…" />;
  }

  if (isError) {
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load audit events"}
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
        title="Audit log"
        description="Security-sensitive organization activity (owner/admin only)."
      />

      <FilterBar>
        <div className="w-48 space-y-1">
          <label className="text-muted-foreground text-xs">Action</label>
          <Input
            value={action}
            onChange={(event) => {
              setAction(event.target.value);
              setPageIndex(0);
            }}
            placeholder="e.g. member.added"
          />
        </div>
        <div className="w-48 space-y-1">
          <label className="text-muted-foreground text-xs">Resource type</label>
          <Input
            value={resourceType}
            onChange={(event) => {
              setResourceType(event.target.value);
              setPageIndex(0);
            }}
            placeholder="e.g. policy_pack"
          />
        </div>
        <div className="w-56 space-y-1">
          <label className="text-muted-foreground text-xs">Actor user id</label>
          <Input
            value={actorUserId}
            onChange={(event) => {
              setActorUserId(event.target.value);
              setPageIndex(0);
            }}
            placeholder="UUID"
          />
        </div>
      </FilterBar>

      {items.length === 0 ? (
        <EmptyState
          icon={<ScrollText />}
          title="No audit events"
          description="Events appear here when members change resources in this organization."
        />
      ) : (
        <DataTable
          columns={columns}
          data={items}
          pagination={{
            pageIndex,
            pageSize: PAGE_SIZE,
            pageCount,
            totalRows: total,
            onPageChange: setPageIndex,
          }}
        />
      )}

      <Sheet
        open={Boolean(selected)}
        onOpenChange={(open) => {
          if (!open) {
            setSelected(null);
          }
        }}
      >
        <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>Audit event</SheetTitle>
          </SheetHeader>
          {selected ? (
            <div className="mt-4 space-y-4 text-sm">
              <dl className="grid gap-3">
                <div>
                  <dt className="text-muted-foreground">Action</dt>
                  <dd className="font-medium">{selected.action}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">When</dt>
                  <dd>{formatDateTime(selected.created_at)}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Actor</dt>
                  <dd className="font-mono text-xs">{selected.actor_user_id ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Resource</dt>
                  <dd>
                    {selected.resource_type}
                    {selected.resource_id ? (
                      <span className="text-muted-foreground ml-1 font-mono text-xs">
                        {selected.resource_id}
                      </span>
                    ) : null}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Request ID</dt>
                  <dd className="font-mono text-xs">{selected.request_id}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">IP</dt>
                  <dd>{selected.ip_address ?? "—"}</dd>
                </div>
              </dl>
              <div className="space-y-2">
                <h3 className="font-medium">Metadata</h3>
                <p className="text-muted-foreground text-xs">
                  Sensitive values are labeled as [REDACTED].
                </p>
                <JsonViewer data={labelRedactedMetadata(selected.metadata_json)} />
              </div>
            </div>
          ) : null}
        </SheetContent>
      </Sheet>
    </div>
  );
}
