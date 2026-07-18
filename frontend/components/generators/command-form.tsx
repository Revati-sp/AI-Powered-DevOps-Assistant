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
import {
  Form,
  FormControl,
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
import { Textarea } from "@/components/ui/textarea";
import { useGenerateCommand } from "@/features/generators/hooks";
import {
  commandFormSchema,
  defaultSaveOptions,
  toSavePayload,
  type CommandFormValues,
} from "@/features/generators/schemas";
import type { GeneratorOutputBase, ShellCommandResponse } from "@/features/generators/types";
import { isApiClientError } from "@/lib/api/errors";
import { useWorkspaceStore } from "@/store/workspace-store";

function toOutput(result: ShellCommandResponse): GeneratorOutputBase {
  return {
    content: result.command,
    command: result.command,
    disclaimer: result.disclaimer,
    explanation: result.explanation ? [result.explanation] : [],
    warnings: result.warnings,
    policy_findings: result.policy_findings,
    saved_artifact_id: result.saved_artifact_id,
    risk_level: result.risk_level,
    requires_confirmation: result.requires_confirmation,
  };
}

export function CommandForm() {
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const mutation = useGenerateCommand();
  const [result, setResult] = React.useState<ShellCommandResponse | null>(null);

  const form = useForm<CommandFormValues>({
    resolver: zodResolver(commandFormSchema),
    defaultValues: {
      ...defaultSaveOptions,
      organization_id: organizationId,
      request: "",
      operating_system: "linux",
      shell: "bash",
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
        request: values.request,
        operating_system: values.operating_system,
        shell: values.shell,
        provider: values.provider,
      });
      setResult(response);
      toast.success(
        response.saved_artifact_id ? "Command generated and saved" : "Command generated",
      );
    } catch (error) {
      toast.error(isApiClientError(error) ? error.message : "Failed to generate command");
    }
  });

  return (
    <GeneratorShell
      title="Shell Command Generator"
      description="Draft explainable shell commands. Suggestions only — nothing is executed."
      form={
        <Form {...form}>
          <form onSubmit={onSubmit} className="space-y-4" noValidate>
            <FormField
              control={form.control}
              name="request"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>What do you need?</FormLabel>
                  <FormControl>
                    <Textarea
                      rows={5}
                      placeholder="List running containers and free disk space on the host"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="operating_system"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Operating system</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="linux">Linux</SelectItem>
                        <SelectItem value="macos">macOS</SelectItem>
                        <SelectItem value="windows">Windows</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="shell"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Shell</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="bash">bash</SelectItem>
                        <SelectItem value="zsh">zsh</SelectItem>
                        <SelectItem value="sh">sh</SelectItem>
                        <SelectItem value="powershell">powershell</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
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
              {mutation.isPending ? "Generating…" : "Generate command"}
            </Button>
          </form>
        </Form>
      }
      output={
        <GeneratorOutput
          result={result ? toOutput(result) : null}
          language="shell"
          filename="command.sh"
          isCommand
          emptyDescription="Describe the task and generate a suggested command. It will not be executed."
          onClear={() => setResult(null)}
          onRegenerate={() => void onSubmit()}
          regenerateDisabled={mutation.isPending}
        />
      }
    />
  );
}
