"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import * as React from "react";
import { useForm } from "react-hook-form";

import { JsonViewer } from "@/components/data-display/json-viewer";
import { Button } from "@/components/ui/button";
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
  isListConfigRuleKey,
  listConfigFieldName,
  POLICY_RESOURCE_TYPES,
  POLICY_SEVERITIES,
  RULE_KEY_LABELS,
  SUPPORTED_RULE_KEYS,
  type SupportedRuleKey,
} from "@/features/policies/constants";
import {
  configurationFromRuleForm,
  policyRuleFormSchema,
  type PolicyRuleFormValues,
} from "@/features/policies/schemas";
import type { PolicyRuleResponse } from "@/features/policies/types";

type RuleBuilderFormProps = {
  initial?: PolicyRuleResponse | null;
  loading?: boolean;
  submitLabel?: string;
  onSubmit: (values: {
    form: PolicyRuleFormValues;
    configuration: Record<string, unknown>;
  }) => Promise<void> | void;
  onCancel?: () => void;
  /** When editing, rule_key and resource_type are locked. */
  lockIdentity?: boolean;
};

function listItemsFromRule(rule?: PolicyRuleResponse | null): string {
  if (!rule || !isListConfigRuleKey(rule.rule_key)) {
    return "";
  }
  const field = listConfigFieldName(rule.rule_key);
  const value = rule.configuration_json?.[field];
  return Array.isArray(value) ? value.map(String).join("\n") : "";
}

export function RuleBuilderForm({
  initial,
  loading = false,
  submitLabel = "Save rule",
  onSubmit,
  onCancel,
  lockIdentity = false,
}: RuleBuilderFormProps) {
  const form = useForm<PolicyRuleFormValues>({
    resolver: zodResolver(policyRuleFormSchema),
    defaultValues: {
      rule_key: (initial?.rule_key as SupportedRuleKey) ?? "require_non_root_container",
      name: initial?.name ?? "",
      description: initial?.description ?? "",
      resource_type:
        (initial?.resource_type as PolicyRuleFormValues["resource_type"]) ?? "dockerfile",
      severity: (initial?.severity as PolicyRuleFormValues["severity"]) ?? "medium",
      remediation: initial?.remediation ?? "",
      is_enabled: initial?.is_enabled ?? true,
      list_items: listItemsFromRule(initial),
    },
  });

  const ruleKey = form.watch("rule_key");
  const listItems = form.watch("list_items");
  const previewConfiguration = React.useMemo(() => {
    return configurationFromRuleForm({
      ...form.getValues(),
      rule_key: ruleKey,
      list_items: listItems,
    });
  }, [form, ruleKey, listItems]);

  React.useEffect(() => {
    if (!isListConfigRuleKey(ruleKey)) {
      form.setValue("list_items", "");
    }
  }, [ruleKey, form]);

  const handleSubmit = form.handleSubmit(async (values) => {
    await onSubmit({
      form: values,
      configuration: configurationFromRuleForm(values),
    });
  });

  return (
    <Form {...form}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormField
          control={form.control}
          name="rule_key"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Rule</FormLabel>
              <Select
                value={field.value}
                onValueChange={field.onChange}
                disabled={loading || lockIdentity}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {SUPPORTED_RULE_KEYS.map((key) => (
                    <SelectItem key={key} value={key}>
                      {RULE_KEY_LABELS[key]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input disabled={loading} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="severity"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Severity</FormLabel>
                <Select value={field.value} onValueChange={field.onChange} disabled={loading}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {POLICY_SEVERITIES.map((severity) => (
                      <SelectItem key={severity} value={severity}>
                        {severity}
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
          name="resource_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Resource type</FormLabel>
              <Select
                value={field.value}
                onValueChange={field.onChange}
                disabled={loading || lockIdentity}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {POLICY_RESOURCE_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
                <Textarea disabled={loading} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {isListConfigRuleKey(ruleKey) ? (
          <FormField
            control={form.control}
            name="list_items"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  {ruleKey === "allowed_container_registries" ? "Registries" : "Labels"}
                </FormLabel>
                <FormControl>
                  <Textarea disabled={loading} placeholder="One per line" {...field} />
                </FormControl>
                <FormDescription>Enter values separated by commas or new lines.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        ) : null}

        <FormField
          control={form.control}
          name="remediation"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Remediation</FormLabel>
              <FormControl>
                <Textarea disabled={loading} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="is_enabled"
          render={({ field }) => (
            <FormItem className="flex items-center justify-between rounded-md border px-3 py-2">
              <FormLabel className="m-0">Enabled</FormLabel>
              <FormControl>
                <Switch checked={field.value} onCheckedChange={field.onChange} disabled={loading} />
              </FormControl>
            </FormItem>
          )}
        />

        <div className="space-y-2">
          <p className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
            Configuration preview (read-only)
          </p>
          <JsonViewer data={previewConfiguration} maxHeight="10rem" />
        </div>

        <div className="flex justify-end gap-2">
          {onCancel ? (
            <Button type="button" variant="outline" disabled={loading} onClick={onCancel}>
              Cancel
            </Button>
          ) : null}
          <Button type="submit" disabled={loading}>
            {loading ? "Saving…" : submitLabel}
          </Button>
        </div>
      </form>
    </Form>
  );
}
