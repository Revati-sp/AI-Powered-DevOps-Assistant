"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { CodeEditor, type EditorLanguage } from "@/components/editors/code-editor";
import { DiffEditor } from "@/components/editors/diff-editor";
import { PageHeader } from "@/components/data-display/page-header";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { FindingCard } from "@/components/reviews/finding-card";
import { FindingsFilters, type FindingsFiltersValue } from "@/components/reviews/findings-filters";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useReviewConfiguration } from "@/features/reviews/hooks";
import { reviewFormSchema, type ReviewFormValues } from "@/features/reviews/schemas";
import type { ReviewFinding, ReviewResponse, ReviewType } from "@/features/reviews/types";
import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { components } from "@/lib/api/generated-types";
import { isApiClientError } from "@/lib/api/errors";
import { queryKeys } from "@/lib/api/query-keys";
import { LLM_PROVIDERS } from "@/lib/constants/app";
import { useWorkspaceStore } from "@/store/workspace-store";

type PolicyPacksPage = components["schemas"]["Page_PolicyPackResponse_"];

const REVIEW_TYPES: Array<{ value: ReviewType; label: string }> = [
  { value: "dockerfile", label: "Dockerfile" },
  { value: "kubernetes", label: "Kubernetes" },
  { value: "terraform", label: "Terraform" },
  { value: "github-actions", label: "GitHub Actions" },
];

function editorLanguageFor(type: ReviewType): EditorLanguage {
  switch (type) {
    case "dockerfile":
      return "dockerfile";
    case "kubernetes":
    case "github-actions":
      return "yaml";
    case "terraform":
      return "hcl";
    default:
      return "plaintext";
  }
}

function mergeFindings(result: ReviewResponse): ReviewFinding[] {
  if (result.findings && result.findings.length > 0) {
    return result.findings;
  }
  return [
    ...(result.built_in_findings ?? []),
    ...(result.organization_policy_findings ?? []),
    ...(result.llm_findings ?? []),
  ];
}

function filterFindings(findings: ReviewFinding[], filters: FindingsFiltersValue): ReviewFinding[] {
  return findings.filter((finding) => {
    if (filters.severity !== "all" && finding.severity !== filters.severity) {
      return false;
    }
    if (filters.source !== "all" && finding.source !== filters.source) {
      return false;
    }
    return true;
  });
}

export function ReviewWorkspace() {
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const mutation = useReviewConfiguration();
  const [result, setResult] = React.useState<ReviewResponse | null>(null);
  const [filters, setFilters] = React.useState<FindingsFiltersValue>({
    severity: "all",
    source: "all",
  });
  const [includePolicies, setIncludePolicies] = React.useState(false);

  const form = useForm<ReviewFormValues>({
    resolver: zodResolver(reviewFormSchema),
    defaultValues: {
      type: "dockerfile",
      content: "",
      provider: "gemini",
      organization_id: organizationId,
      policy_pack_ids: [],
    },
  });

  React.useEffect(() => {
    form.setValue("organization_id", organizationId);
  }, [organizationId, form]);

  const reviewType = form.watch("type");
  const selectedPackIds = form.watch("policy_pack_ids");

  const packsQuery = useQuery({
    queryKey: queryKeys.policyPacks.list(organizationId ?? "none"),
    queryFn: () =>
      apiFetch<PolicyPacksPage>(
        `${endpoints.policies.packs(organizationId as string)}?limit=100&offset=0`,
      ),
    enabled: Boolean(organizationId && includePolicies),
  });

  const packs = packsQuery.data?.items.filter((p) => p.is_active) ?? [];

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      const response = await mutation.mutateAsync({
        type: values.type,
        content: values.content,
        provider: values.provider,
        organization_id: includePolicies ? organizationId : null,
        policy_pack_ids: includePolicies ? values.policy_pack_ids : [],
      });
      setResult(response);
      setFilters({ severity: "all", source: "all" });
      toast.success("Review complete");
    } catch (error) {
      toast.error(isApiClientError(error) ? error.message : "Failed to review configuration");
    }
  });

  const allFindings = result ? mergeFindings(result) : [];
  const visibleFindings = filterFindings(allFindings, filters);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Configuration Review"
        description="Review infrastructure and application configuration against policy and best practices."
      />

      <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
        <Form {...form}>
          <form onSubmit={onSubmit} className="space-y-4" noValidate>
            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Configuration type</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {REVIEW_TYPES.map((item) => (
                        <SelectItem key={item.value} value={item.value}>
                          {item.label}
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
              name="content"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Content</FormLabel>
                  <FormControl>
                    <CodeEditor
                      value={field.value}
                      onChange={(value) => field.onChange(value ?? "")}
                      language={editorLanguageFor(reviewType)}
                      height="320px"
                      path={`review.${reviewType}`}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="provider"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Provider</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {LLM_PROVIDERS.map((provider) => (
                        <SelectItem key={provider} value={provider}>
                          {provider}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-3 rounded-md border p-4">
              <label className="flex items-start gap-3 text-sm">
                <Checkbox
                  checked={includePolicies}
                  onCheckedChange={(checked) => {
                    const enabled = checked === true;
                    setIncludePolicies(enabled);
                    if (enabled && organizationId) {
                      form.setValue("organization_id", organizationId);
                    }
                  }}
                  disabled={!organizationId}
                />
                <span>
                  <span className="font-medium">Include organization policies</span>
                  <FormDescription>
                    {organizationId
                      ? "Attach active policy packs from the selected organization."
                      : "Select an organization in the header to enable policy review."}
                  </FormDescription>
                </span>
              </label>

              {includePolicies && packs.length > 0 ? (
                <FormField
                  control={form.control}
                  name="policy_pack_ids"
                  render={() => (
                    <FormItem>
                      <FormLabel>Policy packs</FormLabel>
                      <FormDescription>Leave empty to use all active packs.</FormDescription>
                      <div className="mt-2 space-y-2">
                        {packs.map((pack) => {
                          const checked = selectedPackIds.includes(pack.id);
                          return (
                            <label key={pack.id} className="flex items-center gap-2 text-sm">
                              <Checkbox
                                checked={checked}
                                onCheckedChange={(value) => {
                                  const next =
                                    value === true
                                      ? [...selectedPackIds, pack.id]
                                      : selectedPackIds.filter((id) => id !== pack.id);
                                  form.setValue("policy_pack_ids", next);
                                }}
                              />
                              <span>{pack.name}</span>
                            </label>
                          );
                        })}
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ) : null}
            </div>

            {mutation.isError && isApiClientError(mutation.error) ? (
              <ErrorState
                message={mutation.error.message}
                requestId={mutation.error.requestId}
                className="py-4"
              />
            ) : null}

            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Reviewing…" : "Run review"}
            </Button>
          </form>
        </Form>

        <div className="space-y-4">
          {!result ? (
            <div className="rounded-md border">
              <EmptyState
                title="Ready for review"
                description="Submit a configuration to receive findings, severity ratings, and remediation guidance."
              />
            </div>
          ) : (
            <>
              <div className="space-y-3 rounded-md border p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="secondary">Score: {result.score}</Badge>
                  <span className="text-muted-foreground text-xs">
                    AI-generated output — review before use.
                  </span>
                </div>
                <p className="text-sm">{result.summary}</p>
                {result.disclaimer ? (
                  <p className="text-muted-foreground text-xs">{result.disclaimer}</p>
                ) : null}
              </div>

              <FindingsFilters
                value={filters}
                onChange={setFilters}
                counts={{
                  total: allFindings.length,
                  visible: visibleFindings.length,
                }}
              />

              {visibleFindings.length === 0 ? (
                <EmptyState
                  title="No matching findings"
                  description="Try adjusting severity or source filters."
                  className="rounded-md border py-8"
                />
              ) : (
                <div className="space-y-3">
                  {visibleFindings.map((finding, index) => (
                    <FindingCard
                      key={`${finding.source}-${finding.title}-${finding.line ?? index}`}
                      finding={finding}
                    />
                  ))}
                </div>
              )}

              {result.improved_content ? (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Suggested improvements</p>
                  <DiffEditor
                    original={form.getValues("content")}
                    modified={result.improved_content}
                    language={editorLanguageFor(reviewType)}
                    readOnly
                    height="360px"
                  />
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
