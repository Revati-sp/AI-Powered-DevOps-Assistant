"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { CodeEditor } from "@/components/editors/code-editor";
import { PageHeader } from "@/components/data-display/page-header";
import { SeverityBadge } from "@/components/data-display/severity-badge";
import { CopyButton } from "@/components/data-display/copy-button";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
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
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  isTaskActive,
  parseTaskLogResult,
  useAnalyzeLogsAsyncMutation,
  useAnalyzeLogsMutation,
  useAnalyzeLogsUploadMutation,
  useLogAnalysisTask,
} from "@/features/logs/hooks";
import { validateLogFile, looksLikeBinaryText } from "@/features/logs/file-validation";
import {
  LOG_ASYNC_THRESHOLD,
  LOG_CONTENT_MAX,
  logAnalyzePasteSchema,
  type LogAnalyzePasteValues,
} from "@/features/logs/schemas";
import type { LogAnalyzeResult } from "@/features/logs/types";
import { isApiClientError } from "@/lib/api/errors";
import { LLM_PROVIDERS } from "@/lib/constants/app";
import { StatusBadge } from "@/components/data-display/status-badge";

function ResultsPanel({ result }: { result: LogAnalyzeResult }) {
  return (
    <div className="space-y-4 rounded-md border p-4">
      <div className="flex flex-wrap items-center gap-2">
        <SeverityBadge severity={result.severity} />
        <Badge variant="secondary">Confidence: {Math.round(result.confidence * 100)}%</Badge>
      </div>

      <div>
        <p className="text-sm font-medium">Summary</p>
        <p className="text-muted-foreground mt-1 text-sm">{result.summary}</p>
      </div>

      {(
        [
          ["Detected errors", result.detected_errors],
          ["Possible causes", result.possible_causes],
          ["Recommended actions", result.recommended_actions],
        ] as const
      ).map(([title, items]) =>
        items && items.length > 0 ? (
          <div key={title}>
            <p className="text-sm font-medium">{title}</p>
            <ul className="text-muted-foreground mt-1 list-disc space-y-1 pl-5 text-sm">
              {items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null,
      )}

      {result.diagnostic_commands && result.diagnostic_commands.length > 0 ? (
        <div className="space-y-2">
          <p className="text-sm font-medium">Diagnostic commands</p>
          <p className="text-muted-foreground text-xs">
            Commands are suggestions only and have not been executed.
          </p>
          <ul className="space-y-2">
            {result.diagnostic_commands.map((cmd) => (
              <li
                key={cmd}
                className="bg-muted/40 flex items-start gap-2 rounded-md border p-2 font-mono text-xs"
              >
                <span className="flex-1 break-all">{cmd}</span>
                <CopyButton value={cmd} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {result.disclaimer ? (
        <p className="text-muted-foreground text-xs">{result.disclaimer}</p>
      ) : null}
    </div>
  );
}

export function LogAnalyzer() {
  const [tab, setTab] = React.useState<"paste" | "upload">("paste");
  const [result, setResult] = React.useState<LogAnalyzeResult | null>(null);
  const [taskId, setTaskId] = React.useState<string | null>(null);
  const [uploadProvider, setUploadProvider] =
    React.useState<(typeof LLM_PROVIDERS)[number]>("gemini");
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);

  const syncMutation = useAnalyzeLogsMutation();
  const asyncMutation = useAnalyzeLogsAsyncMutation();
  const uploadMutation = useAnalyzeLogsUploadMutation();
  const taskQuery = useLogAnalysisTask(taskId);

  const form = useForm<LogAnalyzePasteValues>({
    resolver: zodResolver(logAnalyzePasteSchema),
    defaultValues: {
      content: "",
      provider: "gemini",
      async_mode: false,
    },
  });

  const content = form.watch("content");
  const suggestAsync = content.length >= LOG_ASYNC_THRESHOLD;

  React.useEffect(() => {
    if (suggestAsync && !form.getValues("async_mode")) {
      form.setValue("async_mode", true);
    }
  }, [suggestAsync, form]);

  React.useEffect(() => {
    const task = taskQuery.data;
    if (!task) return;

    if (task.status === "succeeded") {
      const parsed = parseTaskLogResult(task.result_json);
      if (parsed) {
        setResult(parsed);
        toast.success("Log analysis complete");
      } else {
        toast.error("Task finished but result could not be parsed");
      }
      setTaskId(null);
    } else if (task.status === "failed" || task.status === "cancelled") {
      toast.error(task.error_message ?? `Analysis ${task.status}`);
      setTaskId(null);
    }
  }, [taskQuery.data]);

  const onPasteSubmit = form.handleSubmit(async (values) => {
    setResult(null);
    setTaskId(null);
    try {
      if (values.async_mode) {
        const idempotencyKey =
          typeof crypto !== "undefined" && "randomUUID" in crypto
            ? crypto.randomUUID()
            : `log-${Date.now()}`;
        const asyncResult = await asyncMutation.mutateAsync({
          content: values.content,
          provider: values.provider,
          idempotencyKey,
        });
        setTaskId(asyncResult.task_id);
        toast.message("Analysis queued", {
          description: `Task ${asyncResult.task_id}`,
        });
        return;
      }

      const syncResult = await syncMutation.mutateAsync({
        content: values.content,
        provider: values.provider,
        async_mode: false,
      });
      setResult(syncResult);
      toast.success("Log analysis complete");
    } catch (error) {
      toast.error(isApiClientError(error) ? error.message : "Failed to analyze logs");
    }
  });

  async function onUploadSubmit(event: React.FormEvent) {
    event.preventDefault();
    setUploadError(null);
    setResult(null);
    setTaskId(null);

    const validation = validateLogFile(selectedFile);
    if (!validation.ok) {
      setUploadError(validation.error.message);
      return;
    }

    try {
      const text = await validation.file.text();
      if (looksLikeBinaryText(text)) {
        setUploadError("Uploaded file appears to be binary, not text.");
        return;
      }
      if (text.length > LOG_CONTENT_MAX) {
        setUploadError(`File content exceeds ${LOG_CONTENT_MAX} characters.`);
        return;
      }

      const uploadResult = await uploadMutation.mutateAsync({
        file: validation.file,
        provider: uploadProvider,
      });
      setResult(uploadResult);
      toast.success("Log analysis complete");
    } catch (error) {
      const message = isApiClientError(error) ? error.message : "Failed to analyze uploaded log";
      setUploadError(message);
      toast.error(message);
    }
  }

  const isPending =
    syncMutation.isPending ||
    asyncMutation.isPending ||
    uploadMutation.isPending ||
    isTaskActive(taskQuery.data?.status);

  const taskProgress = taskQuery.data?.progress ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Log Analyzer"
        description="Paste or upload logs to surface root causes, severity, and suggested next steps."
      />

      <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
        <div className="space-y-4">
          <Tabs value={tab} onValueChange={(value) => setTab(value as "paste" | "upload")}>
            <TabsList>
              <TabsTrigger value="paste">Paste</TabsTrigger>
              <TabsTrigger value="upload">Upload</TabsTrigger>
            </TabsList>

            <TabsContent value="paste" className="mt-4 space-y-4">
              <Form {...form}>
                <form onSubmit={onPasteSubmit} className="space-y-4" noValidate>
                  <FormField
                    control={form.control}
                    name="content"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Log content</FormLabel>
                        <FormControl>
                          <CodeEditor
                            value={field.value}
                            onChange={(value) => field.onChange(value ?? "")}
                            language="plaintext"
                            height="280px"
                            path="logs.txt"
                          />
                        </FormControl>
                        <FormDescription>
                          {field.value.length.toLocaleString()} / {LOG_CONTENT_MAX.toLocaleString()}{" "}
                          characters
                        </FormDescription>
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
                  <FormField
                    control={form.control}
                    name="async_mode"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-start gap-3 space-y-0">
                        <FormControl>
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={(v) => field.onChange(v === true)}
                          />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <FormLabel>Run asynchronously</FormLabel>
                          <FormDescription>
                            Recommended for large logs
                            {suggestAsync ? " (auto-enabled for this size)" : ""}. Polls task status
                            until complete.
                          </FormDescription>
                        </div>
                      </FormItem>
                    )}
                  />
                  <Button type="submit" disabled={isPending}>
                    {isPending ? "Analyzing…" : "Analyze logs"}
                  </Button>
                </form>
              </Form>
            </TabsContent>

            <TabsContent value="upload" className="mt-4 space-y-4">
              <form onSubmit={onUploadSubmit} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="log-file">
                    Log file (.log or .txt)
                  </label>
                  <Input
                    id="log-file"
                    type="file"
                    accept=".log,.txt,text/plain"
                    onChange={(event) => {
                      setUploadError(null);
                      setSelectedFile(event.target.files?.[0] ?? null);
                    }}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Provider</label>
                  <Select
                    value={uploadProvider}
                    onValueChange={(value) => setUploadProvider(value as typeof uploadProvider)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {LLM_PROVIDERS.map((provider) => (
                        <SelectItem key={provider} value={provider}>
                          {provider}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {uploadError ? <ErrorState message={uploadError} className="py-4" /> : null}
                <Button type="submit" disabled={isPending || !selectedFile}>
                  {isPending ? "Analyzing…" : "Upload & analyze"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </div>

        <div className="space-y-4">
          {taskId && isTaskActive(taskQuery.data?.status) ? (
            <div className="space-y-3 rounded-md border p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium">Async analysis in progress</p>
                {taskQuery.data?.status ? <StatusBadge status={taskQuery.data.status} /> : null}
              </div>
              <Progress value={Math.min(100, Math.max(0, taskProgress))} />
              <p className="text-muted-foreground text-xs">
                Task ID: <span className="font-mono">{taskId}</span>
              </p>
              <LoadingState label="Waiting for analysis results…" />
            </div>
          ) : null}

          {result ? (
            <ResultsPanel result={result} />
          ) : !taskId ? (
            <div className="rounded-md border">
              <EmptyState
                title="No analysis yet"
                description="Paste log text or upload a file to get severity, causes, and suggested diagnostics."
              />
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
