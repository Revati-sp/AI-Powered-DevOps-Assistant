"use client";

import { SeverityBadge } from "@/components/data-display/severity-badge";
import { Badge } from "@/components/ui/badge";
import { FINDING_SOURCE_LABELS, type ReviewFinding } from "@/features/reviews/types";

export type FindingCardProps = {
  finding: ReviewFinding;
};

export function FindingCard({ finding }: FindingCardProps) {
  return (
    <article className="space-y-2 rounded-md border p-3">
      <div className="flex flex-wrap items-center gap-2">
        <SeverityBadge severity={finding.severity} />
        <Badge variant="outline">{FINDING_SOURCE_LABELS[finding.source]}</Badge>
        {finding.line != null ? (
          <span className="text-muted-foreground text-xs">Line {finding.line}</span>
        ) : null}
        {finding.rule_key ? (
          <span className="text-muted-foreground font-mono text-xs">{finding.rule_key}</span>
        ) : null}
      </div>
      <h3 className="text-sm font-semibold">{finding.title}</h3>
      <p className="text-muted-foreground text-sm">{finding.description}</p>
      {finding.recommendation ? (
        <p className="text-sm">
          <span className="font-medium">Recommendation: </span>
          {finding.recommendation}
        </p>
      ) : null}
    </article>
  );
}
