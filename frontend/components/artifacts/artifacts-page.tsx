"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import type { ColumnDef } from "@tanstack/react-table";
import { FileCode2, Plus } from "lucide-react";
import Link from "next/link";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { useOrgRole } from "@/components/app-shell/use-org-role";
import { DataTable } from "@/components/data-display/data-table";
import { FilterBar } from "@/components/data-display/filter-bar";
import { PageHeader } from "@/components/data-display/page-header";
import { CodeEditor } from "@/components/editors/code-editor";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
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
import { Textarea } from "@/components/ui/textarea";
import {
  ARTIFACT_TYPE_LABELS,
  ARTIFACT_TYPES,
  artifactTypeLabel,
} from "@/features/artifacts/constants";
import { useArtifacts, useCreateArtifact } from "@/features/artifacts/hooks";
import { artifactCreateSchema, type ArtifactCreateFormValues } from "@/features/artifacts/schemas";
import type { ArtifactSummaryResponse, ArtifactType } from "@/features/artifacts/types";
import { isApiClientError } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/formatters/date";
import { useWorkspaceStore } from "@/store/workspace-store";

const PAGE_SIZE = 20;

export function ArtifactsPageClient() {
  const role = useOrgRole();
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const [pageIndex, setPageIndex] = React.useState(0);
  const [createOpen, setCreateOpen] = React.useState(false);
  const [typeFilter, setTypeFilter] = React.useState<string>("all");

  const filters = {
    organization_id: organizationId,
    limit: PAGE_SIZE,
    offset: pageIndex * PAGE_SIZE,
  };

  const { data, isLoading, isError, error, refetch } = useArtifacts(filters);
  const createMutation = useCreateArtifact();

  const form = useForm<ArtifactCreateFormValues>({
    resolver: zodResolver(artifactCreateSchema),
    defaultValues: {
      name: "",
      description: "",
      artifact_type: "dockerfile",
      content: "",
    },
  });

  React.useEffect(() => {
    if (createOpen) {
      form.reset({
        name: "",
        description: "",
        artifact_type: "dockerfile",
        content: "",
      });
    }
  }, [createOpen, form]);

  const items = React.useMemo(() => {
    const rows = data?.items ?? [];
    if (typeFilter === "all") {
      return rows;
    }
    return rows.filter((item) => item.artifact_type === typeFilter);
  }, [data?.items, typeFilter]);

  const columns = React.useMemo<ColumnDef<ArtifactSummaryResponse>[]>(
    () => [
      {
        accessorKey: "name",
        header: "Name",
        cell: ({ row }) => (
          <Link
            href={`/artifacts/${row.original.id}`}
            className="text-primary font-medium hover:underline"
          >
            {row.original.name}
          </Link>
        ),
      },
      {
        accessorKey: "artifact_type",
        header: "Type",
        cell: ({ row }) => artifactTypeLabel(row.original.artifact_type),
      },
      {
        accessorKey: "current_version_number",
        header: "Version",
        cell: ({ row }) => row.original.current_version_number ?? "—",
      },
      {
        accessorKey: "updated_at",
        header: "Updated",
        cell: ({ row }) => formatDateTime(row.original.updated_at),
      },
    ],
    [],
  );

  const handleCreate = form.handleSubmit(async (values) => {
    try {
      const artifact = await createMutation.mutateAsync({
        name: values.name,
        description: values.description || null,
        artifact_type: values.artifact_type as ArtifactType,
        content: values.content,
        organization_id: organizationId,
      });
      toast.success(`Created ${artifact.name}`);
      setCreateOpen(false);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to create artifact");
    }
  });

  if (isLoading) {
    return <LoadingState label="Loading artifacts…" />;
  }

  if (isError) {
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load artifacts"}
        requestId={isApiClientError(error) ? error.requestId : undefined}
        onRetry={() => void refetch()}
      />
    );
  }

  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Artifacts"
        description="Versioned infrastructure and DevOps artifacts for this workspace."
        actions={
          <PermissionGate permission="artifact.write" role={role}>
            <Button type="button" onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              New artifact
            </Button>
          </PermissionGate>
        }
      />

      <FilterBar>
        <div className="w-48 space-y-1">
          <label className="text-muted-foreground text-xs">Type</label>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger>
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {ARTIFACT_TYPES.map((type) => (
                <SelectItem key={type} value={type}>
                  {ARTIFACT_TYPE_LABELS[type]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </FilterBar>

      {items.length === 0 ? (
        <EmptyState
          icon={<FileCode2 />}
          title="No artifacts yet"
          description="Create an artifact or generate one from the generators."
          action={
            <PermissionGate permission="artifact.write" role={role}>
              <Button type="button" onClick={() => setCreateOpen(true)}>
                <Plus className="h-4 w-4" />
                New artifact
              </Button>
            </PermissionGate>
          }
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

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Create artifact</DialogTitle>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Name</FormLabel>
                      <FormControl>
                        <Input disabled={createMutation.isPending} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="artifact_type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Type</FormLabel>
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                        disabled={createMutation.isPending}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {ARTIFACT_TYPES.map((type) => (
                            <SelectItem key={type} value={type}>
                              {ARTIFACT_TYPE_LABELS[type]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea disabled={createMutation.isPending} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="content"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Content</FormLabel>
                    <FormControl>
                      <CodeEditor
                        value={field.value}
                        onChange={(value) => field.onChange(value ?? "")}
                        height="280px"
                        language="plaintext"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  disabled={createMutation.isPending}
                  onClick={() => setCreateOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? "Creating…" : "Create"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
