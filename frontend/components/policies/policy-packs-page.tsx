"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import type { ColumnDef } from "@tanstack/react-table";
import { Shield } from "lucide-react";
import Link from "next/link";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { useOrganizationRole } from "@/components/app-shell/use-org-role";
import { DataTable } from "@/components/data-display/data-table";
import { PageHeader } from "@/components/data-display/page-header";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PermissionDenied } from "@/components/feedback/permission-denied";
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
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { useCreatePolicyPack, usePolicyPacks } from "@/features/policies/hooks";
import { policyPackFormSchema, type PolicyPackFormValues } from "@/features/policies/schemas";
import type { PolicyPackResponse } from "@/features/policies/types";
import { isApiClientError } from "@/lib/api/errors";
import { can } from "@/lib/permissions/rbac";
import { useWorkspaceStore } from "@/store/workspace-store";

const PAGE_SIZE = 20;

type PolicyPacksPageProps = {
  organizationId: string;
};

export function PolicyPacksPageClient({ organizationId }: PolicyPacksPageProps) {
  const role = useOrganizationRole(organizationId);
  const setOrganization = useWorkspaceStore((s) => s.setOrganization);
  const [pageIndex, setPageIndex] = React.useState(0);
  const [createOpen, setCreateOpen] = React.useState(false);

  React.useEffect(() => {
    setOrganization(organizationId);
  }, [organizationId, setOrganization]);

  const { data, isLoading, isError, error, refetch } = usePolicyPacks(organizationId, {
    limit: PAGE_SIZE,
    offset: pageIndex * PAGE_SIZE,
  });
  const createMutation = useCreatePolicyPack(organizationId);

  const form = useForm<PolicyPackFormValues>({
    resolver: zodResolver(policyPackFormSchema),
    defaultValues: { name: "", description: "", is_active: true },
  });

  React.useEffect(() => {
    if (createOpen) {
      form.reset({ name: "", description: "", is_active: true });
    }
  }, [createOpen, form]);

  const columns = React.useMemo<ColumnDef<PolicyPackResponse>[]>(
    () => [
      {
        accessorKey: "name",
        header: "Name",
        cell: ({ row }) => (
          <Link
            href={`/organizations/${organizationId}/policies/${row.original.id}`}
            className="text-primary font-medium hover:underline"
          >
            {row.original.name}
          </Link>
        ),
      },
      {
        accessorKey: "is_active",
        header: "Status",
        cell: ({ row }) => (
          <Badge variant={row.original.is_active ? "default" : "secondary"}>
            {row.original.is_active ? "Active" : "Inactive"}
          </Badge>
        ),
      },
      {
        accessorKey: "version",
        header: "Version",
      },
    ],
    [organizationId],
  );

  const handleCreate = form.handleSubmit(async (values) => {
    try {
      await createMutation.mutateAsync({
        name: values.name,
        description: values.description || null,
        is_active: values.is_active,
      });
      toast.success("Policy pack created");
      setCreateOpen(false);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to create policy pack");
    }
  });

  if (isLoading) {
    return <LoadingState label="Loading policy packs…" />;
  }

  if (isError) {
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load policy packs"}
        requestId={isApiClientError(error) ? error.requestId : undefined}
        onRetry={() => void refetch()}
      />
    );
  }

  if (role && !can(role, "policy.read")) {
    return <PermissionDenied />;
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Policy packs"
        description="Organization policy packs and evaluation rules."
        actions={
          <PermissionGate permission="policy.manage" role={role}>
            <Button type="button" onClick={() => setCreateOpen(true)}>
              New pack
            </Button>
          </PermissionGate>
        }
      />

      {items.length === 0 ? (
        <EmptyState
          icon={<Shield />}
          title="No policy packs"
          description="Create a pack to define security and compliance rules."
          action={
            <PermissionGate permission="policy.manage" role={role}>
              <Button type="button" onClick={() => setCreateOpen(true)}>
                New pack
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
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create policy pack</DialogTitle>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={handleCreate} className="space-y-4">
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
                name="is_active"
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-md border px-3 py-2">
                    <FormLabel className="m-0">Active</FormLabel>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        disabled={createMutation.isPending}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  Create
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
