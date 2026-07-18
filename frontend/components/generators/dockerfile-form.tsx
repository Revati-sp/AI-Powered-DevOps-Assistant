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
import { useGenerateDockerfile } from "@/features/generators/hooks";
import {
  defaultSaveOptions,
  dockerfileFormSchema,
  toSavePayload,
  type DockerfileFormValues,
} from "@/features/generators/schemas";
import type { DockerfileResponse } from "@/features/generators/types";
import { isApiClientError } from "@/lib/api/errors";
import { useWorkspaceStore } from "@/store/workspace-store";

export function DockerfileForm() {
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const mutation = useGenerateDockerfile();
  const [result, setResult] = React.useState<DockerfileResponse | null>(null);

  const form = useForm<DockerfileFormValues>({
    resolver: zodResolver(dockerfileFormSchema),
    defaultValues: {
      ...defaultSaveOptions,
      organization_id: organizationId,
      language: "python",
      framework: "",
      python_version: "3.12",
      port: 8000,
      use_multistage: true,
      run_as_non_root: true,
      provider: "gemini",
    },
  });

  React.useEffect(() => {
    form.setValue("organization_id", organizationId);
  }, [organizationId, form]);

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      const response = await mutation.mutateAsync({
        ...toSavePayload(values),
        language: values.language,
        framework: values.framework.trim() || null,
        python_version: values.python_version,
        port: values.port,
        use_multistage: values.use_multistage,
        run_as_non_root: values.run_as_non_root,
        provider: values.provider,
      });
      setResult(response);
      toast.success(
        response.saved_artifact_id ? "Dockerfile generated and saved" : "Dockerfile generated",
      );
    } catch (error) {
      const message = isApiClientError(error) ? error.message : "Failed to generate Dockerfile";
      toast.error(message);
    }
  });

  return (
    <GeneratorShell
      title="Dockerfile Generator"
      description="Describe your runtime and get a production-minded Dockerfile."
      form={
        <Form {...form}>
          <form onSubmit={onSubmit} className="space-y-4" noValidate>
            <FormField
              control={form.control}
              name="language"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Language</FormLabel>
                  <FormControl>
                    <Input placeholder="python" {...field} />
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
                  <FormLabel>Framework (optional)</FormLabel>
                  <FormControl>
                    <Input placeholder="fastapi" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="python_version"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Python version</FormLabel>
                    <FormControl>
                      <Input placeholder="3.12" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="port"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Port</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        value={field.value}
                        onBlur={field.onBlur}
                        name={field.name}
                        ref={field.ref}
                        onChange={(event) => field.onChange(event.target.valueAsNumber)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="use_multistage"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center gap-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={(v) => field.onChange(v === true)}
                    />
                  </FormControl>
                  <FormLabel>Use multi-stage build</FormLabel>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="run_as_non_root"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center gap-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={(v) => field.onChange(v === true)}
                    />
                  </FormControl>
                  <FormLabel>Run as non-root</FormLabel>
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
              {mutation.isPending ? "Generating…" : "Generate Dockerfile"}
            </Button>
          </form>
        </Form>
      }
      output={
        <GeneratorOutput
          result={result}
          language="dockerfile"
          filename="Dockerfile"
          onClear={() => setResult(null)}
          onRegenerate={() => void onSubmit()}
          regenerateDisabled={mutation.isPending}
        />
      }
    />
  );
}
