"use client";

import Link from "next/link";
import { Eraser, RefreshCw } from "lucide-react";

import { CodeEditor, type EditorLanguage } from "@/components/editors/code-editor";
import { CopyButton } from "@/components/data-display/copy-button";
import { DownloadButton } from "@/components/data-display/download-button";
import { SeverityBadge } from "@/components/data-display/severity-badge";
import { EmptyState } from "@/components/feedback/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { GeneratorOutputBase } from "@/features/generators/types";
import type { PolicyFinding } from "@/features/generators/types";
import type { Severity } from "@/components/data-display/severity-badge";

export type GeneratorOutputProps = {
  result: GeneratorOutputBase | null;
  language?: EditorLanguage;
  filename?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  onClear?: () => void;
  onRegenerate?: () => void;
  regenerateDisabled?: boolean;
  isCommand?: boolean;
};

function PolicyFindingsList({ findings }: { findings: PolicyFinding[] }) {
  if (findings.length === 0) return null;
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">Policy findings</p>
      <ul className="space-y-2">
        {findings.map((finding) => (
          <li
            key={`${finding.policy_pack_id}-${finding.rule_key}-${finding.title}`}
            className="rounded-md border p-3 text-sm"
          >
            <div className="flex flex-wrap items-center gap-2">
              <SeverityBadge severity={finding.severity as Severity} />
              <span className="font-medium">{finding.title}</span>
              <Badge variant="outline">Organization policy</Badge>
            </div>
            <p className="text-muted-foreground mt-1">{finding.description}</p>
            {finding.recommendation ? (
              <p className="mt-1 text-xs">Recommendation: {finding.recommendation}</p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function GeneratorOutput({
  result,
  language = "plaintext",
  filename = "generated.txt",
  emptyTitle = "No output yet",
  emptyDescription = "Fill in the form and generate to see results here.",
  onClear,
  onRegenerate,
  regenerateDisabled,
  isCommand = false,
}: GeneratorOutputProps) {
  if (!result) {
    return (
      <div className="rounded-md border">
        <EmptyState title={emptyTitle} description={emptyDescription} />
      </div>
    );
  }

  const content = isCommand ? (result.command ?? result.content) : result.content;

  return (
    <div className="space-y-4 rounded-md border p-4">
      <div className="bg-muted/50 rounded-md border px-3 py-2 text-xs">
        AI-generated output — review before use.
      </div>

      {result.disclaimer ? (
        <p className="text-muted-foreground text-xs">{result.disclaimer}</p>
      ) : null}

      {isCommand && result.risk_level ? (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-muted-foreground">Risk:</span>
          <SeverityBadge severity={result.risk_level} />
          {result.requires_confirmation ? (
            <Badge variant="warning">Requires confirmation</Badge>
          ) : null}
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-2">
        <CopyButton value={content} />
        <DownloadButton content={content} filename={filename} size="sm" />
        {onRegenerate ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onRegenerate}
            disabled={regenerateDisabled}
          >
            <RefreshCw />
            Regenerate
          </Button>
        ) : null}
        {onClear ? (
          <Button type="button" variant="ghost" size="sm" onClick={onClear}>
            <Eraser />
            Clear
          </Button>
        ) : null}
        {result.saved_artifact_id ? (
          <Button asChild variant="secondary" size="sm">
            <Link href={`/artifacts/${result.saved_artifact_id}`}>View saved artifact</Link>
          </Button>
        ) : null}
      </div>

      <CodeEditor value={content} language={language} readOnly height="360px" path={filename} />

      {result.warnings && result.warnings.length > 0 ? (
        <div className="space-y-1">
          <p className="text-sm font-medium">Warnings</p>
          <ul className="text-muted-foreground list-disc space-y-1 pl-5 text-sm">
            {result.warnings.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {result.explanation && result.explanation.length > 0 ? (
        <div className="space-y-1">
          <p className="text-sm font-medium">Explanation</p>
          <ul className="text-muted-foreground list-disc space-y-1 pl-5 text-sm">
            {result.explanation.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {result.best_practices && result.best_practices.length > 0 ? (
        <div className="space-y-1">
          <p className="text-sm font-medium">Best practices</p>
          <ul className="text-muted-foreground list-disc space-y-1 pl-5 text-sm">
            {result.best_practices.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <PolicyFindingsList findings={result.policy_findings ?? []} />
    </div>
  );
}
