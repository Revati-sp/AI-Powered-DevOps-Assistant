"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import type { ColumnDef } from "@tanstack/react-table";
import { useRouter } from "next/navigation";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { useOrganizationRole } from "@/components/app-shell/use-org-role";
import { DataTable } from "@/components/data-display/data-table";
import { PageHeader } from "@/components/data-display/page-header";
import { SeverityBadge } from "@/components/data-display/severity-badge";
import { RuleBuilderForm } from "@/components/policies/rule-builder-form";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PermissionDenied } from "@/components/feedback/permission-denied";
import { PermissionGate } from "@/components/permissions/permission-gate";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
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
import { RULE_KEY_LABELS, type SupportedRuleKey } from "@/features/policies/constants";
import {
  useCreatePolicyRule,
  useDeletePolicyPack,
  useDeletePolicyRule,
  usePolicyPack,
  useUpdatePolicyPack,
  useUpdatePolicyRule,
} from "@/features/policies/hooks";
import {
  policyPackFormSchema,
  type PolicyPackFormValues,
  type PolicyRuleFormValues,
} from "@/features/policies/schemas";
import type { PolicyRuleResponse } from "@/features/policies/types";
import { isApiClientError } from "@/lib/api/errors";
import { can } from "@/lib/permissions/rbac";
import type { Severity } from "@/components/data-display/severity-badge";
import { useWorkspaceStore } from "@/store/workspace-store";

type PolicyPackDetailProps = {
  organizationId: string;
  policyPackId: string;
};

export function PolicyPackDetail({ organizationId, policyPackId }: PolicyPackDetailProps) {
  const router = useRouter();
  const role = useOrganizationRole(organizationId);
  const setOrganization = useWorkspaceStore((s) => s.setOrganization);
  const [editOpen, setEditOpen] = React.useState(false);
  const [deleteOpen, setDeleteOpen] = React.useState(false);
  const [ruleOpen, setRuleOpen] = React.useState(false);
  const [editingRule, setEditingRule] = React.useState<PolicyRuleResponse | null>(null);
  const [deletingRule, setDeletingRule] = React.useState<PolicyRuleResponse | null>(null);

  React.useEffect(() => {
    setOrganization(organizationId);
  }, [organizationId, setOrganization]);

  const { data, isLoading, isError, error, refetch } = usePolicyPack(organizationId, policyPackId);
  const updatePack = useUpdatePolicyPack(organizationId, policyPackId);
  const deletePack = useDeletePolicyPack(organizationId);
  const createRule = useCreatePolicyRule(organizationId, policyPackId);
  const updateRule = useUpdatePolicyRule(organizationId, policyPackId);
  const deleteRule = useDeletePolicyRule(organizationId, policyPackId);

  const packForm = useForm<PolicyPackFormValues>({
    resolver: zodResolver(policyPackFormSchema),
    defaultValues: { name: "", description: "", is_active: true },
  });

  React.useEffect(() => {
    if (editOpen && data) {
      packForm.reset({
        name: data.name,
        description: data.description ?? "",
        is_active: data.is_active,
      });
    }
  }, [editOpen, data, packForm]);

  const rules = data?.rules ?? [];

  const columns = React.useMemo<ColumnDef<PolicyRuleResponse>[]>(
    () => [
      {
        accessorKey: "name",
        header: "Name",
        cell: ({ row }) => (
          <div>
            <div className="font-medium">{row.original.name}</div>
            <div className="text-muted-foreground text-xs">
              {RULE_KEY_LABELS[row.original.rule_key as SupportedRuleKey] ?? row.original.rule_key}
            </div>
          </div>
        ),
      },
      {
        accessorKey: "resource_type",
        header: "Resource",
      },
      {
        accessorKey: "severity",
        header: "Severity",
        cell: ({ row }) => <SeverityBadge severity={row.original.severity as Severity} />,
      },
      {
        accessorKey: "is_enabled",
        header: "Enabled",
        cell: ({ row }) => (
          <Badge variant={row.original.is_enabled ? "default" : "secondary"}>
            {row.original.is_enabled ? "On" : "Off"}
          </Badge>
        ),
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <PermissionGate permission="policy.manage" role={role}>
            <div className="flex gap-1">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  setEditingRule(row.original);
                  setRuleOpen(true);
                }}
              >
                Edit
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setDeletingRule(row.original)}
              >
                Delete
              </Button>
            </div>
          </PermissionGate>
        ),
      },
    ],
    [role],
  );

  const handleUpdatePack = packForm.handleSubmit(async (values) => {
    try {
      await updatePack.mutateAsync({
        name: values.name,
        description: values.description || null,
        is_active: values.is_active,
      });
      toast.success("Policy pack updated");
      setEditOpen(false);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to update policy pack");
    }
  });

  const handleDeletePack = async () => {
    try {
      await deletePack.mutateAsync(policyPackId);
      toast.success("Policy pack deleted");
      router.push(`/organizations/${organizationId}/policies`);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to delete policy pack");
    }
  };

  const handleRuleSubmit = async ({
    form,
    configuration,
  }: {
    form: PolicyRuleFormValues;
    configuration: Record<string, unknown>;
  }) => {
    try {
      if (editingRule) {
        await updateRule.mutateAsync({
          ruleId: editingRule.id,
          body: {
            name: form.name,
            description: form.description,
            severity: form.severity,
            configuration,
            remediation: form.remediation || null,
            is_enabled: form.is_enabled,
          },
        });
        toast.success("Rule updated");
      } else {
        await createRule.mutateAsync({
          rule_key: form.rule_key,
          name: form.name,
          description: form.description,
          resource_type: form.resource_type,
          severity: form.severity,
          configuration,
          remediation: form.remediation || null,
          is_enabled: form.is_enabled,
        });
        toast.success("Rule created");
      }
      setRuleOpen(false);
      setEditingRule(null);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to save rule");
    }
  };

  const handleDeleteRule = async () => {
    if (!deletingRule) {
      return;
    }
    try {
      await deleteRule.mutateAsync(deletingRule.id);
      toast.success("Rule deleted");
      setDeletingRule(null);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to delete rule");
    }
  };

  if (isLoading) {
    return <LoadingState label="Loading policy pack…" />;
  }

  if (isError || !data) {
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load policy pack"}
        requestId={isApiClientError(error) ? error.requestId : undefined}
        onRetry={() => void refetch()}
      />
    );
  }

  if (role && !can(role, "policy.read")) {
    return <PermissionDenied />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={data.name}
        description={data.description ?? "Policy pack rules"}
        actions={
          <PermissionGate permission="policy.manage" role={role}>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" onClick={() => setEditOpen(true)}>
                Edit pack
              </Button>
              <Button
                type="button"
                onClick={() => {
                  setEditingRule(null);
                  setRuleOpen(true);
                }}
              >
                Add rule
              </Button>
              <Button type="button" variant="destructive" onClick={() => setDeleteOpen(true)}>
                Delete pack
              </Button>
            </div>
          </PermissionGate>
        }
      />

      <div className="flex flex-wrap gap-2">
        <Badge variant={data.is_active ? "default" : "secondary"}>
          {data.is_active ? "Active" : "Inactive"}
        </Badge>
        <Badge variant="outline">v{data.version}</Badge>
      </div>

      <DataTable columns={columns} data={rules} emptyMessage="No rules in this pack yet." />

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit policy pack</DialogTitle>
          </DialogHeader>
          <Form {...packForm}>
            <form onSubmit={handleUpdatePack} className="space-y-4">
              <FormField
                control={packForm.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input disabled={updatePack.isPending} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={packForm.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea disabled={updatePack.isPending} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={packForm.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-md border px-3 py-2">
                    <FormLabel className="m-0">Active</FormLabel>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        disabled={updatePack.isPending}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setEditOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={updatePack.isPending}>
                  Save
                </Button>
              </div>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={ruleOpen}
        onOpenChange={(open) => {
          setRuleOpen(open);
          if (!open) {
            setEditingRule(null);
          }
        }}
      >
        <DialogContent className="max-h-[90vh] max-w-xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingRule ? "Edit rule" : "Add rule"}</DialogTitle>
          </DialogHeader>
          <RuleBuilderForm
            key={editingRule?.id ?? "new"}
            initial={editingRule}
            lockIdentity={Boolean(editingRule)}
            loading={createRule.isPending || updateRule.isPending}
            submitLabel={editingRule ? "Update rule" : "Create rule"}
            onCancel={() => {
              setRuleOpen(false);
              setEditingRule(null);
            }}
            onSubmit={handleRuleSubmit}
          />
        </DialogContent>
      </Dialog>

      <ConfirmationDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete policy pack?"
        description="This deletes the pack and all of its rules."
        confirmLabel="Delete"
        variant="destructive"
        loading={deletePack.isPending}
        onConfirm={() => void handleDeletePack()}
      />

      <ConfirmationDialog
        open={Boolean(deletingRule)}
        onOpenChange={(open) => {
          if (!open) {
            setDeletingRule(null);
          }
        }}
        title="Delete rule?"
        description={deletingRule ? `Remove “${deletingRule.name}” from this pack?` : undefined}
        confirmLabel="Delete"
        variant="destructive"
        loading={deleteRule.isPending}
        onConfirm={() => void handleDeleteRule()}
      />
    </div>
  );
}
