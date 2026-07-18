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
import { useGenerateKubernetes } from "@/features/generators/hooks";
import {
  defaultSaveOptions,
  kubernetesFormSchema,
  toSavePayload,
  type KubernetesFormValues,
} from "@/features/generators/schemas";
import type { KubernetesResponse } from "@/features/generators/types";
import { isApiClientError } from "@/lib/api/errors";
import { useWorkspaceStore } from "@/store/workspace-store";

export function KubernetesForm() {
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const mutation = useGenerateKubernetes();
  const [result, setResult] = React.useState<KubernetesResponse | null>(null);

  const form = useForm<KubernetesFormValues>({
    resolver: zodResolver(kubernetesFormSchema),
    defaultValues: {
      ...defaultSaveOptions,
      organization_id: organizationId,
      application_name: "my-app",
      image: "ghcr.io/example/my-app:latest",
      replicas: 2,
      container_port: 8000,
      service_type: "ClusterIP",
      include_ingress: false,
      include_configmap: true,
      include_hpa: true,
      cpu_request: "100m",
      cpu_limit: "500m",
      memory_request: "128Mi",
      memory_limit: "512Mi",
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
        application_name: values.application_name,
        image: values.image,
        replicas: values.replicas,
        container_port: values.container_port,
        service_type: values.service_type,
        include_ingress: values.include_ingress,
        include_configmap: values.include_configmap,
        include_hpa: values.include_hpa,
        cpu_request: values.cpu_request,
        cpu_limit: values.cpu_limit,
        memory_request: values.memory_request,
        memory_limit: values.memory_limit,
        provider: values.provider,
      });
      setResult(response);
      toast.success(
        response.saved_artifact_id ? "Manifests generated and saved" : "Manifests generated",
      );
    } catch (error) {
      toast.error(
        isApiClientError(error) ? error.message : "Failed to generate Kubernetes manifests",
      );
    }
  });

  return (
    <GeneratorShell
      title="Kubernetes Generator"
      description="Produce Deployment, Service, and related manifests for common workloads."
      form={
        <Form {...form}>
          <form onSubmit={onSubmit} className="space-y-4" noValidate>
            <FormField
              control={form.control}
              name="application_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Application name</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="image"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Image</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="replicas"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Replicas</FormLabel>
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
              <FormField
                control={form.control}
                name="container_port"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Container port</FormLabel>
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
              name="service_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Service type</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="ClusterIP">ClusterIP</SelectItem>
                      <SelectItem value="NodePort">NodePort</SelectItem>
                      <SelectItem value="LoadBalancer">LoadBalancer</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid gap-3 sm:grid-cols-3">
              {(
                [
                  ["include_ingress", "Include Ingress"],
                  ["include_configmap", "Include ConfigMap"],
                  ["include_hpa", "Include HPA"],
                ] as const
              ).map(([name, label]) => (
                <FormField
                  key={name}
                  control={form.control}
                  name={name}
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-2 space-y-0">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={(v) => field.onChange(v === true)}
                        />
                      </FormControl>
                      <FormLabel className="text-xs">{label}</FormLabel>
                    </FormItem>
                  )}
                />
              ))}
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              {(
                [
                  ["cpu_request", "CPU request"],
                  ["cpu_limit", "CPU limit"],
                  ["memory_request", "Memory request"],
                  ["memory_limit", "Memory limit"],
                ] as const
              ).map(([name, label]) => (
                <FormField
                  key={name}
                  control={form.control}
                  name={name}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{label}</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ))}
            </div>
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
              {mutation.isPending ? "Generating…" : "Generate manifests"}
            </Button>
          </form>
        </Form>
      }
      output={
        <GeneratorOutput
          result={result}
          language="yaml"
          filename="k8s.yaml"
          onClear={() => setResult(null)}
          onRegenerate={() => void onSubmit()}
          regenerateDisabled={mutation.isPending}
        />
      }
    />
  );
}
