"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import type { ColumnDef } from "@tanstack/react-table";
import { AlertTriangle, BarChart3, Gauge } from "lucide-react";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { useOrgRole } from "@/components/app-shell/use-org-role";
import { DataTable } from "@/components/data-display/data-table";
import { PageHeader } from "@/components/data-display/page-header";
import { SectionHeader } from "@/components/data-display/section-header";
import { StatCard } from "@/components/data-display/stat-card";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PermissionGate } from "@/components/permissions/permission-gate";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  useMyUsage,
  useOrganizationUsage,
  usePatchOrganizationQuotas,
} from "@/features/usage/hooks";
import {
  getUsageLimitStatus,
  quotaFormSchema,
  type QuotaFormValues,
} from "@/features/usage/schemas";
import type { UsageEventResponse } from "@/features/usage/types";
import { isApiClientError } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/formatters/date";
import { cn } from "@/lib/utils/cn";
import { useWorkspaceStore } from "@/store/workspace-store";

function formatCount(value: number): string {
  return new Intl.NumberFormat().format(value);
}

function UsageLimitBadge({
  used,
  limit,
  label,
}: {
  used: number;
  limit: number | null | undefined;
  label: string;
}) {
  const status = getUsageLimitStatus(used, limit);
  if (status === "ok" || limit == null) {
    return null;
  }

  return (
    <Badge variant={status === "over" ? "danger" : "warning"} className="gap-1">
      <AlertTriangle className="h-3 w-3" aria-hidden />
      {status === "over" ? `${label} limit exceeded` : `${label} nearing limit`}
    </Badge>
  );
}

function UsageStatCard({
  label,
  used,
  limit,
  estimated,
}: {
  label: string;
  used: number;
  limit?: number | null;
  estimated?: boolean;
}) {
  const status = getUsageLimitStatus(used, limit);

  return (
    <StatCard
      label={label}
      value={formatCount(used)}
      description={
        limit != null
          ? `${formatCount(used)} / ${formatCount(limit)} used`
          : estimated
            ? "Estimated from token usage"
            : undefined
      }
      icon={<BarChart3 />}
      className={cn(
        status === "warning" && "border-warning/50",
        status === "over" && "border-danger/50",
      )}
    />
  );
}

export function UsagePageClient() {
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const role = useOrgRole();

  const myUsageQuery = useMyUsage();
  const orgUsageQuery = useOrganizationUsage(organizationId);
  const patchQuotas = usePatchOrganizationQuotas(organizationId ?? "");

  const quota = orgUsageQuery.data?.quota;

  const form = useForm<QuotaFormValues>({
    resolver: zodResolver(quotaFormSchema),
    defaultValues: {
      daily_token_limit: null,
      daily_request_limit: null,
      monthly_token_limit: null,
      monthly_request_limit: null,
      enforce_quotas: false,
      clear_daily_limits: false,
      clear_monthly_limits: false,
    },
  });

  React.useEffect(() => {
    if (quota) {
      form.reset({
        daily_token_limit: quota.daily_token_limit,
        daily_request_limit: quota.daily_request_limit,
        monthly_token_limit: quota.monthly_token_limit,
        monthly_request_limit: quota.monthly_request_limit,
        enforce_quotas: quota.enforce_quotas,
        clear_daily_limits: false,
        clear_monthly_limits: false,
      });
    }
  }, [quota, form]);

  const eventColumns = React.useMemo<ColumnDef<UsageEventResponse>[]>(
    () => [
      {
        accessorKey: "created_at",
        header: "Time",
        cell: ({ row }) => formatDateTime(row.original.created_at),
      },
      { accessorKey: "operation", header: "Operation" },
      { accessorKey: "provider", header: "Provider" },
      {
        accessorKey: "total_tokens",
        header: "Tokens",
        cell: ({ row }) => formatCount(row.original.total_tokens),
      },
      {
        accessorKey: "is_estimated",
        header: "Estimated",
        cell: ({ row }) => (row.original.is_estimated ? "Yes" : "No"),
      },
    ],
    [],
  );

  const handleQuotaSubmit = form.handleSubmit(async (values) => {
    if (!organizationId) {
      return;
    }
    try {
      await patchQuotas.mutateAsync({
        daily_token_limit: values.daily_token_limit,
        daily_request_limit: values.daily_request_limit,
        monthly_token_limit: values.monthly_token_limit,
        monthly_request_limit: values.monthly_request_limit,
        enforce_quotas: values.enforce_quotas,
        clear_daily_limits: values.clear_daily_limits,
        clear_monthly_limits: values.clear_monthly_limits,
      });
      toast.success("Organization quotas updated");
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to update quotas");
    }
  });

  if (myUsageQuery.isLoading) {
    return <LoadingState label="Loading usage…" />;
  }

  if (myUsageQuery.isError) {
    return (
      <ErrorState
        message={
          isApiClientError(myUsageQuery.error)
            ? myUsageQuery.error.message
            : "Failed to load usage"
        }
        requestId={
          isApiClientError(myUsageQuery.error) ? myUsageQuery.error.requestId : undefined
        }
        onRetry={() => void myUsageQuery.refetch()}
      />
    );
  }

  const myUsage = myUsageQuery.data;
  const orgUsage = orgUsageQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Usage"
        description="Track LLM token and request consumption for your account and workspace."
      />

      <SectionHeader title="Personal usage" description="Your activity across all workspaces." />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <UsageStatCard
          label="Daily tokens"
          used={myUsage?.daily.tokens ?? 0}
          estimated={myUsage?.daily.estimated}
        />
        <UsageStatCard
          label="Daily requests"
          used={myUsage?.daily.requests ?? 0}
          estimated={myUsage?.daily.estimated}
        />
        <UsageStatCard
          label="Monthly tokens"
          used={myUsage?.monthly.tokens ?? 0}
          estimated={myUsage?.monthly.estimated}
        />
        <UsageStatCard
          label="Monthly requests"
          used={myUsage?.monthly.requests ?? 0}
          estimated={myUsage?.monthly.estimated}
        />
      </div>

      <SectionHeader title="Recent events" description="Latest LLM usage recorded for your account." />
      <DataTable
        columns={eventColumns}
        data={myUsage?.recent_events ?? []}
        emptyMessage="No usage events yet."
      />

      {organizationId ? (
        <>
          <SectionHeader
            title="Organization usage"
            description="Aggregated usage for the selected workspace."
          />

          {orgUsageQuery.isLoading ? (
            <LoadingState label="Loading organization usage…" />
          ) : orgUsageQuery.isError ? (
            <ErrorState
              message={
                isApiClientError(orgUsageQuery.error)
                  ? orgUsageQuery.error.message
                  : "Failed to load organization usage"
              }
              onRetry={() => void orgUsageQuery.refetch()}
            />
          ) : orgUsage ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <UsageLimitBadge
                  used={orgUsage.daily.tokens}
                  limit={quota?.daily_token_limit}
                  label="Daily tokens"
                />
                <UsageLimitBadge
                  used={orgUsage.daily.requests}
                  limit={quota?.daily_request_limit}
                  label="Daily requests"
                />
                <UsageLimitBadge
                  used={orgUsage.monthly.tokens}
                  limit={quota?.monthly_token_limit}
                  label="Monthly tokens"
                />
                <UsageLimitBadge
                  used={orgUsage.monthly.requests}
                  limit={quota?.monthly_request_limit}
                  label="Monthly requests"
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <UsageStatCard
                  label="Org daily tokens"
                  used={orgUsage.daily.tokens}
                  limit={quota?.daily_token_limit}
                  estimated={orgUsage.daily.estimated}
                />
                <UsageStatCard
                  label="Org daily requests"
                  used={orgUsage.daily.requests}
                  limit={quota?.daily_request_limit}
                  estimated={orgUsage.daily.estimated}
                />
                <UsageStatCard
                  label="Org monthly tokens"
                  used={orgUsage.monthly.tokens}
                  limit={quota?.monthly_token_limit}
                  estimated={orgUsage.monthly.estimated}
                />
                <UsageStatCard
                  label="Org monthly requests"
                  used={orgUsage.monthly.requests}
                  limit={quota?.monthly_request_limit}
                  estimated={orgUsage.monthly.estimated}
                />
              </div>

              {quota ? (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Gauge className="h-4 w-4" aria-hidden />
                      Quota settings
                    </CardTitle>
                    <CardDescription>
                      {quota.enforce_quotas
                        ? "Quotas are enforced for this organization."
                        : "Quotas are tracked but not enforced."}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <PermissionGate permission="organization.update" role={role}>
                      <Form {...form}>
                        <form onSubmit={handleQuotaSubmit} className="space-y-4">
                          <div className="grid gap-4 sm:grid-cols-2">
                            <FormField
                              control={form.control}
                              name="daily_token_limit"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Daily token limit</FormLabel>
                                  <FormControl>
                                    <Input
                                      type="number"
                                      min={0}
                                      placeholder="Unlimited"
                                      value={field.value ?? ""}
                                      onChange={(event) =>
                                        field.onChange(
                                          event.target.value === ""
                                            ? null
                                            : Number(event.target.value),
                                        )
                                      }
                                    />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={form.control}
                              name="daily_request_limit"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Daily request limit</FormLabel>
                                  <FormControl>
                                    <Input
                                      type="number"
                                      min={0}
                                      placeholder="Unlimited"
                                      value={field.value ?? ""}
                                      onChange={(event) =>
                                        field.onChange(
                                          event.target.value === ""
                                            ? null
                                            : Number(event.target.value),
                                        )
                                      }
                                    />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={form.control}
                              name="monthly_token_limit"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Monthly token limit</FormLabel>
                                  <FormControl>
                                    <Input
                                      type="number"
                                      min={0}
                                      placeholder="Unlimited"
                                      value={field.value ?? ""}
                                      onChange={(event) =>
                                        field.onChange(
                                          event.target.value === ""
                                            ? null
                                            : Number(event.target.value),
                                        )
                                      }
                                    />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={form.control}
                              name="monthly_request_limit"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Monthly request limit</FormLabel>
                                  <FormControl>
                                    <Input
                                      type="number"
                                      min={0}
                                      placeholder="Unlimited"
                                      value={field.value ?? ""}
                                      onChange={(event) =>
                                        field.onChange(
                                          event.target.value === ""
                                            ? null
                                            : Number(event.target.value),
                                        )
                                      }
                                    />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                          </div>

                          <FormField
                            control={form.control}
                            name="enforce_quotas"
                            render={({ field }) => (
                              <FormItem className="flex items-center justify-between rounded-lg border p-3">
                                <div className="space-y-0.5">
                                  <FormLabel>Enforce quotas</FormLabel>
                                  <FormDescription>
                                    Block LLM requests when limits are exceeded.
                                  </FormDescription>
                                </div>
                                <FormControl>
                                  <Switch checked={field.value} onCheckedChange={field.onChange} />
                                </FormControl>
                              </FormItem>
                            )}
                          />

                          <div className="flex flex-wrap gap-4">
                            <div className="flex items-center gap-2">
                              <Switch
                                id="clear-daily"
                                checked={form.watch("clear_daily_limits")}
                                onCheckedChange={(checked) =>
                                  form.setValue("clear_daily_limits", checked)
                                }
                              />
                              <Label htmlFor="clear-daily">Clear daily limits on save</Label>
                            </div>
                            <div className="flex items-center gap-2">
                              <Switch
                                id="clear-monthly"
                                checked={form.watch("clear_monthly_limits")}
                                onCheckedChange={(checked) =>
                                  form.setValue("clear_monthly_limits", checked)
                                }
                              />
                              <Label htmlFor="clear-monthly">Clear monthly limits on save</Label>
                            </div>
                          </div>

                          <Button type="submit" disabled={patchQuotas.isPending}>
                            {patchQuotas.isPending ? "Saving…" : "Save quotas"}
                          </Button>
                        </form>
                      </Form>
                    </PermissionGate>
                  </CardContent>
                </Card>
              ) : null}
            </div>
          ) : null}
        </>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Organization usage</CardTitle>
            <CardDescription>
              Select an organization from the workspace switcher to view team usage and quotas.
            </CardDescription>
          </CardHeader>
        </Card>
      )}
    </div>
  );
}
