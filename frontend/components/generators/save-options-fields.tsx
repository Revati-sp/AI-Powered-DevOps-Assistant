"use client";

import { useQuery } from "@tanstack/react-query";
import type { FieldValues, Path, UseFormReturn } from "react-hook-form";

import { PermissionGate } from "@/components/permissions/permission-gate";
import { useOrgRole } from "@/components/app-shell/use-org-role";
import { Checkbox } from "@/components/ui/checkbox";
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { components } from "@/lib/api/generated-types";
import { queryKeys } from "@/lib/api/query-keys";
import { useWorkspaceStore } from "@/store/workspace-store";

type PolicyPacksPage = components["schemas"]["Page_PolicyPackResponse_"];

type SaveFields = {
  save_artifact: boolean;
  artifact_name: string;
  artifact_description: string;
  organization_id?: string | null;
  policy_pack_ids: string[];
  validate_policies: boolean;
};

type SaveOptionsFieldsProps<T extends FieldValues & SaveFields> = {
  form: UseFormReturn<T>;
};

export function SaveOptionsFields<T extends FieldValues & SaveFields>({
  form,
}: SaveOptionsFieldsProps<T>) {
  const role = useOrgRole();
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);

  const packsQuery = useQuery({
    queryKey: queryKeys.policyPacks.list(organizationId ?? "none"),
    queryFn: () =>
      apiFetch<PolicyPacksPage>(
        `${endpoints.policies.packs(organizationId as string)}?limit=100&offset=0`,
      ),
    enabled: Boolean(organizationId),
  });

  const packs = packsQuery.data?.items.filter((p) => p.is_active) ?? [];

  return (
    <div className="space-y-4 rounded-md border p-4">
      <div>
        <p className="text-sm font-medium">Save & policy options</p>
        <p className="text-muted-foreground text-xs">
          Optional: persist the result as an artifact and validate against org policy packs.
        </p>
      </div>

      {!organizationId ? (
        <p className="text-muted-foreground text-xs">
          Select an organization in the header to enable saving and policy validation.
        </p>
      ) : (
        <p className="text-muted-foreground text-xs">
          Organization: <span className="font-mono">{organizationId}</span>
        </p>
      )}

      <PermissionGate
        permission="artifact.write"
        role={role}
        fallback={
          organizationId ? (
            <p className="text-muted-foreground text-xs">
              You need artifact write permission to save generated output.
            </p>
          ) : null
        }
      >
        <FormField
          control={form.control}
          name={"save_artifact" as Path<T>}
          render={({ field }) => (
            <FormItem className="flex flex-row items-start gap-3 space-y-0">
              <FormControl>
                <Checkbox
                  checked={Boolean(field.value)}
                  onCheckedChange={(checked) => {
                    field.onChange(checked === true);
                    if (checked === true && organizationId) {
                      form.setValue("organization_id" as Path<T>, organizationId as never);
                    }
                  }}
                  disabled={!organizationId}
                />
              </FormControl>
              <div className="space-y-1 leading-none">
                <FormLabel>Save as artifact</FormLabel>
                <FormDescription>
                  Store the generated content in the selected organization.
                </FormDescription>
              </div>
            </FormItem>
          )}
        />

        {form.watch("save_artifact" as Path<T>) ? (
          <div className="space-y-3 pl-1">
            <FormField
              control={form.control}
              name={"artifact_name" as Path<T>}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Artifact name</FormLabel>
                  <FormControl>
                    <Input {...field} value={String(field.value ?? "")} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name={"artifact_description" as Path<T>}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea rows={2} {...field} value={String(field.value ?? "")} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        ) : null}
      </PermissionGate>

      <FormField
        control={form.control}
        name={"validate_policies" as Path<T>}
        render={({ field }) => (
          <FormItem className="flex flex-row items-start gap-3 space-y-0">
            <FormControl>
              <Checkbox
                checked={Boolean(field.value)}
                onCheckedChange={(checked) => {
                  field.onChange(checked === true);
                  if (checked === true && organizationId) {
                    form.setValue("organization_id" as Path<T>, organizationId as never);
                  }
                }}
                disabled={!organizationId}
              />
            </FormControl>
            <div className="space-y-1 leading-none">
              <FormLabel>Validate policies</FormLabel>
              <FormDescription>
                Run organization policy packs against the generated output.
              </FormDescription>
              <FormMessage />
            </div>
          </FormItem>
        )}
      />

      {form.watch("validate_policies" as Path<T>) && packs.length > 0 ? (
        <FormField
          control={form.control}
          name={"policy_pack_ids" as Path<T>}
          render={({ field }) => {
            const selected = (field.value as string[]) ?? [];
            return (
              <FormItem>
                <FormLabel>Policy packs</FormLabel>
                <FormDescription>
                  Leave empty to use all active packs for the organization.
                </FormDescription>
                <div className="mt-2 space-y-2">
                  {packs.map((pack) => {
                    const checked = selected.includes(pack.id);
                    return (
                      <label key={pack.id} className="flex items-center gap-2 text-sm">
                        <Checkbox
                          checked={checked}
                          onCheckedChange={(value) => {
                            const next =
                              value === true
                                ? [...selected, pack.id]
                                : selected.filter((id) => id !== pack.id);
                            field.onChange(next);
                          }}
                        />
                        <span>{pack.name}</span>
                      </label>
                    );
                  })}
                </div>
                <FormMessage />
              </FormItem>
            );
          }}
        />
      ) : null}
    </div>
  );
}
