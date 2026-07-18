"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import type { ColumnDef } from "@tanstack/react-table";
import { Archive, FileCode2, Plus, Star } from "lucide-react";
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
import { Badge } from "@/components/ui/badge";
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
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  ARTIFACT_TYPE_LABELS,
  ARTIFACT_TYPES,
  artifactTypeLabel,
} from "@/features/artifacts/constants";
import {
  useArtifactTags,
  useArtifacts,
  useCreateArtifact,
  useFavoriteArtifact,
} from "@/features/artifacts/hooks";
import { artifactCreateSchema, type ArtifactCreateFormValues } from "@/features/artifacts/schemas";
import type { ArtifactSummaryResponse, ArtifactType } from "@/features/artifacts/types";
import { isApiClientError } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/formatters/date";
import { cn } from "@/lib/utils/cn";
import { useWorkspaceStore } from "@/store/workspace-store";

const PAGE_SIZE = 20;

function useDebouncedValue<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = React.useState(value);
  React.useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}

export function ArtifactsPageClient() {
  const role = useOrgRole();
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const [pageIndex, setPageIndex] = React.useState(0);
  const [createOpen, setCreateOpen] = React.useState(false);
  const [typeFilter, setTypeFilter] = React.useState<string>("all");
  const [searchInput, setSearchInput] = React.useState("");
  const [tagFilter, setTagFilter] = React.useState<string>("all");
  const [favoritesOnly, setFavoritesOnly] = React.useState(false);
  const [includeArchived, setIncludeArchived] = React.useState(false);

  const debouncedSearch = useDebouncedValue(searchInput);

  const filters = {
    organization_id: organizationId,
    limit: PAGE_SIZE,
    offset: pageIndex * PAGE_SIZE,
    search: debouncedSearch || undefined,
    tags: tagFilter !== "all" ? [tagFilter] : undefined,
    favorites_only: favoritesOnly,
    include_archived: includeArchived,
  };

  const { data, isLoading, isError, error, refetch } = useArtifacts(filters);
  const tagsQuery = useArtifactTags({ organization_id: organizationId });
  const createMutation = useCreateArtifact();
  const favoriteMutation = useFavoriteArtifact();

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

  const toggleFavorite = React.useCallback(
    async (artifact: ArtifactSummaryResponse) => {
      try {
        await favoriteMutation.mutateAsync({
          artifactId: artifact.id,
          favorited: Boolean(artifact.is_favorited),
        });
      } catch (err) {
        toast.error(isApiClientError(err) ? err.message : "Failed to update favorite");
      }
    },
    [favoriteMutation],
  );

  const columns = React.useMemo<ColumnDef<ArtifactSummaryResponse>[]>(
    () => [
      {
        id: "favorite",
        header: "",
        cell: ({ row }) => (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            aria-label={row.original.is_favorited ? "Remove from favorites" : "Add to favorites"}
            disabled={favoriteMutation.isPending}
            onClick={() => void toggleFavorite(row.original)}
          >
            <Star
              className={cn(
                "h-4 w-4",
                row.original.is_favorited ? "fill-warning text-warning" : "text-muted-foreground",
              )}
            />
          </Button>
        ),
      },
      {
        accessorKey: "name",
        header: "Name",
        cell: ({ row }) => (
          <div className="space-y-1">
            <Link
              href={`/artifacts/${row.original.id}`}
              className="text-primary font-medium hover:underline"
            >
              {row.original.name}
            </Link>
            {row.original.archived_at ? (
              <Badge variant="secondary" className="gap-1">
                <Archive className="h-3 w-3" aria-hidden />
                Archived
              </Badge>
            ) : null}
          </div>
        ),
      },
      {
        accessorKey: "artifact_type",
        header: "Type",
        cell: ({ row }) => artifactTypeLabel(row.original.artifact_type),
      },
      {
        id: "tags",
        header: "Tags",
        cell: ({ row }) =>
          row.original.tags && row.original.tags.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {row.original.tags.map((tag) => (
                <Badge key={tag} variant="outline">
                  {tag}
                </Badge>
              ))}
            </div>
          ) : (
            "—"
          ),
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
    [favoriteMutation.isPending, toggleFavorite],
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
  const availableTags = tagsQuery.data ?? [];

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
        <div className="min-w-[12rem] flex-1 space-y-1">
          <Label htmlFor="artifact-search">Search</Label>
          <Input
            id="artifact-search"
            placeholder="Search by name…"
            value={searchInput}
            onChange={(event) => {
              setSearchInput(event.target.value);
              setPageIndex(0);
            }}
          />
        </div>
        <div className="w-48 space-y-1">
          <label className="text-muted-foreground text-xs">Type</label>
          <Select
            value={typeFilter}
            onValueChange={(value) => {
              setTypeFilter(value);
              setPageIndex(0);
            }}
          >
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
        <div className="w-48 space-y-1">
          <label className="text-muted-foreground text-xs">Tag</label>
          <Select
            value={tagFilter}
            onValueChange={(value) => {
              setTagFilter(value);
              setPageIndex(0);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="All tags" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All tags</SelectItem>
              {availableTags.map((tag) => (
                <SelectItem key={tag.id} value={tag.name}>
                  {tag.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Switch
              id="favorites-only"
              checked={favoritesOnly}
              onCheckedChange={(checked) => {
                setFavoritesOnly(checked);
                setPageIndex(0);
              }}
            />
            <Label htmlFor="favorites-only">Favorites only</Label>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              id="include-archived"
              checked={includeArchived}
              onCheckedChange={(checked) => {
                setIncludeArchived(checked);
                setPageIndex(0);
              }}
            />
            <Label htmlFor="include-archived">Include archived</Label>
          </div>
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
