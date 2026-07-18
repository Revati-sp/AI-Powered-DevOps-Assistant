"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import type { ColumnDef } from "@tanstack/react-table";
import { Activity, Pencil, Settings2 } from "lucide-react";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { useOrganizationRole } from "@/components/app-shell/use-org-role";
import { DataTable } from "@/components/data-display/data-table";
import { PageHeader } from "@/components/data-display/page-header";
import { SectionHeader } from "@/components/data-display/section-header";
import { StatCard } from "@/components/data-display/stat-card";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PermissionDenied } from "@/components/feedback/permission-denied";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { operationLabel } from "@/features/providers/constants";
import {
  useAdminProviderConfigs,
  useAdminProviderHealth,
  useAdminProviderRouting,
  useOrgProviderConfigs,
  useOrgProviderRouting,
  usePatchAdminProviderConfig,
  usePatchAdminProviderRouting,
  usePatchOrgProviderConfig,
  usePatchOrgProviderRouting,
} from "@/features/providers/hooks";
import {
  adminProviderConfigPatchSchema,
  providerRoutingPatchSchema,
  type AdminProviderConfigPatchFormValues,
  type ProviderRoutingPatchFormValues,
} from "@/features/providers/schemas";
import type {
  ProviderConfigResponse,
  ProviderHealthResponse,
  ProviderRoutingResponse,
} from "@/features/providers/types";
import { PROVIDER_NAMES } from "@/features/providers/types";
import { isApiClientError } from "@/lib/api/errors";
import { can } from "@/lib/permissions/rbac";
import { useAuth } from "@/providers/auth-provider";

type ProvidersPageProps = {
  organizationId: string;
};

type Scope = "org" | "platform";

function ConfigEditDialog({
  open,
  onOpenChange,
  config,
  scope,
  organizationId,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: ProviderConfigResponse | null;
  scope: Scope;
  organizationId: string;
  onSaved: () => void;
}) {
  const isPlatform = scope === "platform";
  const patchOrg = usePatchOrgProviderConfig(organizationId);
  const patchAdmin = usePatchAdminProviderConfig();

  const form = useForm<AdminProviderConfigPatchFormValues>({
    resolver: zodResolver(adminProviderConfigPatchSchema),
    defaultValues: {
      enabled: true,
      default_model: "",
      timeout_seconds: 60,
      max_retries: 2,
      priority: 0,
      max_output_tokens: 4096,
      secret_env_key: "",
      base_url_env_key: "",
      model_env_key: "",
    },
  });

  React.useEffect(() => {
    if (open && config) {
      form.reset({
        enabled: config.enabled,
        default_model: config.default_model,
        timeout_seconds: config.timeout_seconds,
        max_retries: config.max_retries,
        priority: config.priority,
        max_output_tokens: config.max_output_tokens,
        secret_env_key: "",
        base_url_env_key: config.base_url_env_key ?? "",
        model_env_key: config.model_env_key ?? "",
      });
    }
  }, [open, config, form]);

  const pending = patchOrg.isPending || patchAdmin.isPending;

  const handleSubmit = form.handleSubmit(async (values) => {
    if (!config) {
      return;
    }
    try {
      const body = {
        enabled: values.enabled,
        default_model: values.default_model,
        timeout_seconds: values.timeout_seconds,
        max_retries: values.max_retries,
        priority: values.priority,
        max_output_tokens: values.max_output_tokens,
        ...(isPlatform
          ? {
              secret_env_key: values.secret_env_key || undefined,
              base_url_env_key: values.base_url_env_key || null,
              model_env_key: values.model_env_key || null,
            }
          : {}),
      };

      if (isPlatform) {
        await patchAdmin.mutateAsync({ providerName: config.provider_name, body });
      } else {
        await patchOrg.mutateAsync({ providerName: config.provider_name, body });
      }
      toast.success(`Updated ${config.provider_name}`);
      onOpenChange(false);
      onSaved();
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to update provider");
    }
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Edit {config?.provider_name}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={handleSubmit} className="space-y-4">
            <FormField
              control={form.control}
              name="enabled"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <FormLabel>Enabled</FormLabel>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="default_model"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Default model</FormLabel>
                  <FormControl>
                    <Input disabled={pending} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="timeout_seconds"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Timeout (s)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        disabled={pending}
                        value={field.value}
                        onChange={(event) => field.onChange(Number(event.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="max_retries"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Max retries</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        disabled={pending}
                        value={field.value}
                        onChange={(event) => field.onChange(Number(event.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="priority"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Priority</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        disabled={pending}
                        value={field.value}
                        onChange={(event) => field.onChange(Number(event.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="max_output_tokens"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Max output tokens</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        disabled={pending}
                        value={field.value}
                        onChange={(event) => field.onChange(Number(event.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            {isPlatform ? (
              <>
                <FormField
                  control={form.control}
                  name="secret_env_key"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Secret env key</FormLabel>
                      <FormControl>
                        <Input
                          disabled={pending}
                          placeholder={config?.secret_env_key}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="base_url_env_key"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Base URL env key</FormLabel>
                      <FormControl>
                        <Input disabled={pending} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="model_env_key"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Model env key</FormLabel>
                      <FormControl>
                        <Input disabled={pending} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </>
            ) : null}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={pending}>
                Save
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

function RoutingEditDialog({
  open,
  onOpenChange,
  routing,
  scope,
  organizationId,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  routing: ProviderRoutingResponse | null;
  scope: Scope;
  organizationId: string;
}) {
  const patchOrg = usePatchOrgProviderRouting(organizationId);
  const patchAdmin = usePatchAdminProviderRouting();

  const form = useForm<ProviderRoutingPatchFormValues>({
    resolver: zodResolver(providerRoutingPatchSchema),
    defaultValues: {
      primary_provider: "gemini",
      fallback_providers: [],
    },
  });

  React.useEffect(() => {
    if (open && routing) {
      form.reset({
        primary_provider: routing.primary_provider as ProviderRoutingPatchFormValues["primary_provider"],
        fallback_providers: routing.fallback_providers.filter((name) =>
          PROVIDER_NAMES.includes(name as (typeof PROVIDER_NAMES)[number]),
        ) as ProviderRoutingPatchFormValues["fallback_providers"],
      });
    }
  }, [open, routing, form]);

  const pending = patchOrg.isPending || patchAdmin.isPending;

  const handleSubmit = form.handleSubmit(async (values) => {
    if (!routing) {
      return;
    }
    try {
      const body = {
        primary_provider: values.primary_provider,
        fallback_providers: values.fallback_providers,
      };
      if (scope === "platform") {
        await patchAdmin.mutateAsync({ operation: routing.operation, body });
      } else {
        await patchOrg.mutateAsync({ operation: routing.operation, body });
      }
      toast.success(`Updated routing for ${operationLabel(routing.operation)}`);
      onOpenChange(false);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to update routing");
    }
  });

  const toggleFallback = (provider: (typeof PROVIDER_NAMES)[number], checked: boolean) => {
    const current = form.getValues("fallback_providers");
    const primary = form.getValues("primary_provider");
    if (checked && provider !== primary) {
      form.setValue("fallback_providers", [...current, provider]);
    } else {
      form.setValue(
        "fallback_providers",
        current.filter((item) => item !== provider),
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit routing — {routing ? operationLabel(routing.operation) : ""}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={handleSubmit} className="space-y-4">
            <FormField
              control={form.control}
              name="primary_provider"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Primary provider</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange} disabled={pending}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {PROVIDER_NAMES.map((name) => (
                        <SelectItem key={name} value={name}>
                          {name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="space-y-2">
              <FormLabel>Fallback providers</FormLabel>
              {PROVIDER_NAMES.map((name) => (
                <div key={name} className="flex items-center gap-2">
                  <Checkbox
                    id={`fallback-${name}`}
                    checked={form.watch("fallback_providers").includes(name)}
                    disabled={form.watch("primary_provider") === name || pending}
                    onCheckedChange={(checked) => toggleFallback(name, checked === true)}
                  />
                  <label htmlFor={`fallback-${name}`} className="text-sm capitalize">
                    {name}
                  </label>
                </div>
              ))}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={pending}>
                Save
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

function ProviderConfigsTable({
  configs,
  scope,
  organizationId,
  canEdit,
}: {
  configs: ProviderConfigResponse[];
  scope: Scope;
  organizationId: string;
  canEdit: boolean;
}) {
  const [editConfig, setEditConfig] = React.useState<ProviderConfigResponse | null>(null);

  const columns = React.useMemo<ColumnDef<ProviderConfigResponse>[]>(
    () => [
      {
        accessorKey: "provider_name",
        header: "Provider",
        cell: ({ row }) => <span className="font-medium capitalize">{row.original.provider_name}</span>,
      },
      {
        accessorKey: "enabled",
        header: "Status",
        cell: ({ row }) => (
          <Badge variant={row.original.enabled ? "success" : "secondary"}>
            {row.original.enabled ? "Enabled" : "Disabled"}
          </Badge>
        ),
      },
      { accessorKey: "default_model", header: "Model" },
      { accessorKey: "timeout_seconds", header: "Timeout" },
      { accessorKey: "max_retries", header: "Retries" },
      { accessorKey: "priority", header: "Priority" },
      {
        accessorKey: "secret_env_key",
        header: "Secret env",
        cell: ({ row }) => (
          <span className="font-mono text-xs">{row.original.secret_env_key}</span>
        ),
      },
      {
        accessorKey: "configured",
        header: "Configured",
        cell: ({ row }) => (
          <Badge variant={row.original.configured ? "success" : "warning"}>
            {row.original.configured ? "Yes" : "No"}
          </Badge>
        ),
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) =>
          canEdit ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setEditConfig(row.original)}
            >
              <Pencil className="h-3.5 w-3.5" />
              Edit
            </Button>
          ) : null,
      },
    ],
    [canEdit],
  );

  return (
    <>
      <DataTable columns={columns} data={configs} emptyMessage="No provider configs found." />
      <ConfigEditDialog
        open={editConfig != null}
        onOpenChange={(open) => {
          if (!open) {
            setEditConfig(null);
          }
        }}
        config={editConfig}
        scope={scope}
        organizationId={organizationId}
        onSaved={() => setEditConfig(null)}
      />
    </>
  );
}

function ProviderRoutingTable({
  routing,
  scope,
  organizationId,
  canEdit,
}: {
  routing: ProviderRoutingResponse[];
  scope: Scope;
  organizationId: string;
  canEdit: boolean;
}) {
  const [editRouting, setEditRouting] = React.useState<ProviderRoutingResponse | null>(null);

  const columns = React.useMemo<ColumnDef<ProviderRoutingResponse>[]>(
    () => [
      {
        accessorKey: "operation",
        header: "Operation",
        cell: ({ row }) => operationLabel(row.original.operation),
      },
      {
        accessorKey: "primary_provider",
        header: "Primary",
        cell: ({ row }) => <span className="capitalize">{row.original.primary_provider}</span>,
      },
      {
        accessorKey: "fallback_providers",
        header: "Fallbacks",
        cell: ({ row }) =>
          row.original.fallback_providers.length > 0
            ? row.original.fallback_providers.map((name) => (
                <Badge key={name} variant="outline" className="mr-1 capitalize">
                  {name}
                </Badge>
              ))
            : "—",
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) =>
          canEdit ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setEditRouting(row.original)}
            >
              <Pencil className="h-3.5 w-3.5" />
              Edit
            </Button>
          ) : null,
      },
    ],
    [canEdit],
  );

  return (
    <>
      <DataTable columns={columns} data={routing} emptyMessage="No routing policies found." />
      <RoutingEditDialog
        open={editRouting != null}
        onOpenChange={(open) => {
          if (!open) {
            setEditRouting(null);
          }
        }}
        routing={editRouting}
        scope={scope}
        organizationId={organizationId}
      />
    </>
  );
}

function ProviderHealthCards({ health }: { health: ProviderHealthResponse[] }) {
  if (health.length === 0) {
    return <p className="text-muted-foreground text-sm">No health data available.</p>;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {health.map((item) => (
        <StatCard
          key={item.provider_name}
          label={item.provider_name}
          value={item.circuit_state}
          description={
            item.avg_latency_ms != null
              ? `Avg latency ${Math.round(item.avg_latency_ms)} ms`
              : item.last_failure_category ?? "No recent failures"
          }
          icon={<Activity />}
        />
      ))}
    </div>
  );
}

function ProviderScopePanel({
  scope,
  organizationId,
  canEdit,
}: {
  scope: Scope;
  organizationId: string;
  canEdit: boolean;
}) {
  const isPlatform = scope === "platform";

  const orgConfigsQuery = useOrgProviderConfigs(organizationId, { enabled: !isPlatform });
  const orgRoutingQuery = useOrgProviderRouting(organizationId, { enabled: !isPlatform });
  const adminConfigsQuery = useAdminProviderConfigs({ enabled: isPlatform });
  const adminRoutingQuery = useAdminProviderRouting({ enabled: isPlatform });
  const adminHealthQuery = useAdminProviderHealth({ enabled: isPlatform });

  const configsQuery = isPlatform ? adminConfigsQuery : orgConfigsQuery;
  const routingQuery = isPlatform ? adminRoutingQuery : orgRoutingQuery;

  if (configsQuery.isLoading || routingQuery.isLoading) {
    return <LoadingState label="Loading provider settings…" />;
  }

  if (configsQuery.isError || routingQuery.isError) {
    const error = configsQuery.error ?? routingQuery.error;
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load provider settings"}
        onRetry={() => {
          void configsQuery.refetch();
          void routingQuery.refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-8">
      {isPlatform ? (
        <section className="space-y-4">
          <SectionHeader
            title="Platform health"
            description="Circuit breaker state and latency across global providers."
          />
          {adminHealthQuery.isLoading ? (
            <LoadingState label="Loading health…" />
          ) : adminHealthQuery.isError ? (
            <ErrorState
              message="Failed to load provider health"
              onRetry={() => void adminHealthQuery.refetch()}
            />
          ) : (
            <ProviderHealthCards health={adminHealthQuery.data ?? []} />
          )}
        </section>
      ) : null}

      <section className="space-y-4">
        <SectionHeader
          title="Provider configs"
          description="Enable providers and tune model, timeout, retries, and priority."
        />
        <ProviderConfigsTable
          configs={configsQuery.data ?? []}
          scope={scope}
          organizationId={organizationId}
          canEdit={canEdit}
        />
      </section>

      <section className="space-y-4">
        <SectionHeader
          title="Operation routing"
          description="Primary provider and fallbacks per LLM operation."
        />
        <ProviderRoutingTable
          routing={routingQuery.data ?? []}
          scope={scope}
          organizationId={organizationId}
          canEdit={canEdit}
        />
      </section>
    </div>
  );
}

export function ProvidersPageClient({ organizationId }: ProvidersPageProps) {
  const { user } = useAuth();
  const role = useOrganizationRole(organizationId);
  const isPlatformAdmin = user?.role === "admin";
  const canEditOrg = Boolean(role && can(role, "organization.update"));

  if (!canEditOrg && !isPlatformAdmin) {
    return <PermissionDenied description="You need organization admin access to manage providers." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="LLM Providers"
        description="Configure model providers and routing for this organization. API keys are referenced by environment variable names only."
        actions={
          <Badge variant="outline" className="gap-1">
            <Settings2 className="h-3.5 w-3.5" aria-hidden />
            Env-key references only
          </Badge>
        }
      />

      {isPlatformAdmin ? (
        <Tabs defaultValue="org">
          <TabsList>
            <TabsTrigger value="org">Organization</TabsTrigger>
            <TabsTrigger value="platform">Platform</TabsTrigger>
          </TabsList>
          <TabsContent value="org" className="mt-6">
            <ProviderScopePanel scope="org" organizationId={organizationId} canEdit={canEditOrg} />
          </TabsContent>
          <TabsContent value="platform" className="mt-6">
            <ProviderScopePanel scope="platform" organizationId={organizationId} canEdit />
          </TabsContent>
        </Tabs>
      ) : (
        <ProviderScopePanel scope="org" organizationId={organizationId} canEdit={canEditOrg} />
      )}
    </div>
  );
}
