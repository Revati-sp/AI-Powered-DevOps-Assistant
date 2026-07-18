"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import type { ColumnDef } from "@tanstack/react-table";
import { useRouter } from "next/navigation";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { useOrgRole } from "@/components/app-shell/use-org-role";
import { CodeBlock } from "@/components/data-display/code-block";
import { DataTable } from "@/components/data-display/data-table";
import { PageHeader } from "@/components/data-display/page-header";
import { CodeEditor } from "@/components/editors/code-editor";
import { DiffEditor } from "@/components/editors/diff-editor";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { artifactTypeLabel } from "@/features/artifacts/constants";
import {
  useArtifact,
  useArtifactDiff,
  useArtifactVersion,
  useArtifactVersions,
  useCreateVersion,
  useDeleteArtifact,
  useRestoreVersion,
  useUpdateArtifact,
} from "@/features/artifacts/hooks";
import {
  artifactUpdateSchema,
  artifactVersionSchema,
  type ArtifactUpdateFormValues,
  type ArtifactVersionFormValues,
} from "@/features/artifacts/schemas";
import type { ArtifactVersionResponse } from "@/features/artifacts/types";
import { isApiClientError } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/formatters/date";

type ArtifactDetailProps = {
  artifactId: string;
};

export function ArtifactDetail({ artifactId }: ArtifactDetailProps) {
  const router = useRouter();
  const role = useOrgRole();
  const [editOpen, setEditOpen] = React.useState(false);
  const [versionOpen, setVersionOpen] = React.useState(false);
  const [deleteOpen, setDeleteOpen] = React.useState(false);
  const [restoreVersion, setRestoreVersion] = React.useState<number | null>(null);
  const [fromVersion, setFromVersion] = React.useState<number | null>(null);
  const [toVersion, setToVersion] = React.useState<number | null>(null);

  const { data, isLoading, isError, error, refetch } = useArtifact(artifactId);
  const versionsQuery = useArtifactVersions(artifactId, {
    limit: 50,
    offset: 0,
  });
  const updateMutation = useUpdateArtifact(artifactId);
  const createVersionMutation = useCreateVersion(artifactId);
  const restoreMutation = useRestoreVersion(artifactId);
  const deleteMutation = useDeleteArtifact();

  const versions = versionsQuery.data?.items ?? [];
  const resolvedFromVersion =
    fromVersion ?? (versions.length >= 2 ? (versions[1]?.version_number ?? null) : null);
  const resolvedToVersion =
    toVersion ?? (versions.length >= 1 ? (versions[0]?.version_number ?? null) : null);

  const diffQuery = useArtifactDiff(artifactId, resolvedFromVersion, resolvedToVersion);
  const fromContentQuery = useArtifactVersion(artifactId, resolvedFromVersion);
  const toContentQuery = useArtifactVersion(artifactId, resolvedToVersion);

  const editForm = useForm<ArtifactUpdateFormValues>({
    resolver: zodResolver(artifactUpdateSchema),
    defaultValues: { name: "", description: "" },
  });

  const versionForm = useForm<ArtifactVersionFormValues>({
    resolver: zodResolver(artifactVersionSchema),
    defaultValues: { content: "" },
  });

  React.useEffect(() => {
    if (editOpen && data) {
      editForm.reset({
        name: data.name,
        description: data.description ?? "",
      });
    }
  }, [editOpen, data, editForm]);

  React.useEffect(() => {
    if (versionOpen) {
      versionForm.reset({
        content: data?.current_version?.content ?? "",
      });
    }
  }, [versionOpen, data, versionForm]);

  const versionColumns = React.useMemo<ColumnDef<ArtifactVersionResponse>[]>(
    () => [
      {
        accessorKey: "version_number",
        header: "Version",
        cell: ({ row }) => `v${row.original.version_number}`,
      },
      {
        accessorKey: "content_hash",
        header: "Hash",
        cell: ({ row }) => (
          <span className="font-mono text-xs">{row.original.content_hash.slice(0, 12)}</span>
        ),
      },
      {
        accessorKey: "created_at",
        header: "Created",
        cell: ({ row }) => formatDateTime(row.original.created_at),
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <PermissionGate permission="artifact.write" role={role}>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={row.original.version_number === data?.current_version_number}
              onClick={() => setRestoreVersion(row.original.version_number)}
            >
              Restore
            </Button>
          </PermissionGate>
        ),
      },
    ],
    [data?.current_version_number, role],
  );

  const handleUpdate = editForm.handleSubmit(async (values) => {
    try {
      await updateMutation.mutateAsync({
        name: values.name,
        description: values.description || null,
      });
      toast.success("Artifact updated");
      setEditOpen(false);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to update artifact");
    }
  });

  const handleNewVersion = versionForm.handleSubmit(async (values) => {
    try {
      await createVersionMutation.mutateAsync({ content: values.content });
      toast.success("New version created");
      setVersionOpen(false);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to create version");
    }
  });

  const handleRestore = async () => {
    if (restoreVersion == null) {
      return;
    }
    try {
      const result = await restoreMutation.mutateAsync(restoreVersion);
      toast.success(
        `Restored v${result.restored_from_version} as v${result.new_version.version_number}`,
      );
      setRestoreVersion(null);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to restore version");
    }
  };

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(artifactId);
      toast.success("Artifact deleted");
      router.push("/artifacts");
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to delete artifact");
    }
  };

  if (isLoading) {
    return <LoadingState label="Loading artifact…" />;
  }

  if (isError || !data) {
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load artifact"}
        requestId={isApiClientError(error) ? error.requestId : undefined}
        onRetry={() => void refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={data.name}
        description={`${artifactTypeLabel(data.artifact_type)} · v${data.current_version_number ?? "—"}`}
        actions={
          <div className="flex flex-wrap gap-2">
            <PermissionGate permission="artifact.write" role={role}>
              <Button type="button" variant="outline" onClick={() => setEditOpen(true)}>
                Edit details
              </Button>
              <Button type="button" onClick={() => setVersionOpen(true)}>
                New version
              </Button>
              <Button type="button" variant="destructive" onClick={() => setDeleteOpen(true)}>
                Delete
              </Button>
            </PermissionGate>
          </div>
        }
      />

      {data.description ? (
        <p className="text-muted-foreground text-sm">{data.description}</p>
      ) : null}

      <Tabs defaultValue="content">
        <TabsList>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="versions">Versions</TabsTrigger>
          <TabsTrigger value="diff">Diff</TabsTrigger>
        </TabsList>
        <TabsContent value="content" className="space-y-3">
          <CodeEditor
            value={data.current_version?.content ?? ""}
            readOnly
            height="420px"
            language="plaintext"
          />
        </TabsContent>
        <TabsContent value="versions">
          {versionsQuery.isLoading ? (
            <LoadingState label="Loading versions…" />
          ) : (
            <DataTable columns={versionColumns} data={versions} emptyMessage="No versions yet." />
          )}
        </TabsContent>
        <TabsContent value="diff" className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <div className="w-40 space-y-1">
              <label className="text-muted-foreground text-xs">From</label>
              <Select
                value={resolvedFromVersion != null ? String(resolvedFromVersion) : undefined}
                onValueChange={(value) => setFromVersion(Number(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="From" />
                </SelectTrigger>
                <SelectContent>
                  {versions.map((version) => (
                    <SelectItem key={version.id} value={String(version.version_number)}>
                      v{version.version_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="w-40 space-y-1">
              <label className="text-muted-foreground text-xs">To</label>
              <Select
                value={resolvedToVersion != null ? String(resolvedToVersion) : undefined}
                onValueChange={(value) => setToVersion(Number(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="To" />
                </SelectTrigger>
                <SelectContent>
                  {versions.map((version) => (
                    <SelectItem key={version.id} value={String(version.version_number)}>
                      v{version.version_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {resolvedFromVersion != null && resolvedToVersion != null ? (
            <>
              <DiffEditor
                original={fromContentQuery.data?.content ?? ""}
                modified={toContentQuery.data?.content ?? ""}
                height="360px"
              />
              {diffQuery.data?.diff ? (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">Unified diff</h3>
                  <CodeBlock code={diffQuery.data.diff} language="diff" />
                </div>
              ) : null}
            </>
          ) : (
            <p className="text-muted-foreground text-sm">Select two versions to compare.</p>
          )}
        </TabsContent>
      </Tabs>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit artifact</DialogTitle>
          </DialogHeader>
          <Form {...editForm}>
            <form onSubmit={handleUpdate} className="space-y-4">
              <FormField
                control={editForm.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input disabled={updateMutation.isPending} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={editForm.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea disabled={updateMutation.isPending} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setEditOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={updateMutation.isPending}>
                  Save
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <Dialog open={versionOpen} onOpenChange={setVersionOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Create new version</DialogTitle>
          </DialogHeader>
          <Form {...versionForm}>
            <form onSubmit={handleNewVersion} className="space-y-4">
              <FormField
                control={versionForm.control}
                name="content"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Content</FormLabel>
                    <FormControl>
                      <CodeEditor
                        value={field.value}
                        onChange={(value) => field.onChange(value ?? "")}
                        height="320px"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setVersionOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createVersionMutation.isPending}>
                  Create version
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <ConfirmationDialog
        open={restoreVersion != null}
        onOpenChange={(open) => {
          if (!open) {
            setRestoreVersion(null);
          }
        }}
        title={`Restore v${restoreVersion}?`}
        description="Restoring creates a new version and preserves history."
        confirmLabel="Restore"
        loading={restoreMutation.isPending}
        onConfirm={() => void handleRestore()}
      />

      <ConfirmationDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete artifact?"
        description="This permanently deletes the artifact and its versions."
        confirmLabel="Delete"
        variant="destructive"
        loading={deleteMutation.isPending}
        onConfirm={() => void handleDelete()}
      />
    </div>
  );
}
