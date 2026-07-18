"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { GeneratorOutput } from "@/components/generators/generator-output";
import { GeneratorShell } from "@/components/generators/generator-shell";
import { ProviderField } from "@/components/generators/provider-field";
import { SaveOptionsFields } from "@/components/generators/save-options-fields";
import { ErrorState } from "@/components/feedback/error-state";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
import { useGeneratePipeline } from "@/features/generators/hooks";
import {
  defaultSaveOptions,
  pipelineFormSchema,
  toSavePayload,
  type PipelineFormValues,
} from "@/features/generators/schemas";
import type { PipelineResponse } from "@/features/generators/types";
import { isApiClientError } from "@/lib/api/errors";
import { useWorkspaceStore } from "@/store/workspace-store";

function editorLanguage(platform: PipelineFormValues["platform"]): "yaml" | "groovy" {
  return platform === "jenkins" ? "groovy" : "yaml";
}

export function PipelineForm() {
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const mutation = useGeneratePipeline();
  const [result, setResult] = React.useState<PipelineResponse | null>(null);

  const form = useForm<PipelineFormValues>({
    resolver: zodResolver(pipelineFormSchema),
    defaultValues: {
      ...defaultSaveOptions,
      organization_id: organizationId,
      platform: "github-actions",
      language: "python",
      framework: "fastapi",
      test_command: "pytest",
      build_docker_image: true,
      deploy_target: "kubernetes",
      provider: "gemini",
    },
  });

  React.useEffect(() => {
    form.setValue("organization_id", organizationId);
  }, [organizationId, form]);

  const platform = form.watch("platform");

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      const response = await mutation.mutateAsync({
        ...toSavePayload(values),
        platform: values.platform,
        language: values.language,
        framework: values.framework.trim() || null,
        test_command: values.test_command,
        build_docker_image: values.build_docker_image,
        deploy_target: values.deploy_target,
        provider: values.provider,
      });
      setResult(response);
      toast.success(
        response.saved_artifact_id ? "Pipeline generated and saved" : "Pipeline generated",
      );
    } catch (error) {
      toast.error(isApiClientError(error) ? error.message : "Failed to generate pipeline");
    }
  });

  return (
    <GeneratorShell
      title="CI/CD Pipeline Generator"
      description="Scaffold GitHub Actions, GitLab CI, or Jenkins pipelines."
      form={
        <Form {...form}>
          <form onSubmit={onSubmit} className="space-y-4" noValidate>
            <FormField
              control={form.control}
              name="platform"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Platform</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="github-actions">GitHub Actions</SelectItem>
                      <SelectItem value="gitlab-ci">GitLab CI</SelectItem>
                      <SelectItem value="jenkins">Jenkins</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="language"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Language</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="framework"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Framework</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="test_command"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Test command</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="build_docker_image"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center gap-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={(v) => field.onChange(v === true)}
                    />
                  </FormControl>
                  <FormLabel>Build Docker image</FormLabel>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="deploy_target"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Deploy target</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      <SelectItem value="kubernetes">Kubernetes</SelectItem>
                      <SelectItem value="docker-host">Docker host</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <ProviderField form={form} />
            <SaveOptionsFields form={form} />
            {mutation.isError && isApiClientError(mutation.error) ? (
              <ErrorState
                message={mutation.error.message}
                requestId={mutation.error.requestId}
                className="py-4"
              />
            ) : null}
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Generating…" : "Generate pipeline"}
            </Button>
          </form>
        </Form>
      }
      output={
        <GeneratorOutput
          result={result}
          language={editorLanguage(platform)}
          filename={result?.filename ?? "pipeline.yml"}
          onClear={() => setResult(null)}
          onRegenerate={() => void onSubmit()}
          regenerateDisabled={mutation.isPending}
        />
      }
    />
  );
}
