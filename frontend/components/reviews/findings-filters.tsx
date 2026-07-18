"use client";

import { FilterBar } from "@/components/data-display/filter-bar";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  FINDING_SOURCE_LABELS,
  type FindingSeverity,
  type FindingSource,
} from "@/features/reviews/types";

export type FindingsFiltersValue = {
  severity: FindingSeverity | "all";
  source: FindingSource | "all";
};

export type FindingsFiltersProps = {
  value: FindingsFiltersValue;
  onChange: (value: FindingsFiltersValue) => void;
  counts?: {
    total: number;
    visible: number;
  };
};

const SEVERITIES: Array<FindingSeverity | "all"> = [
  "all",
  "critical",
  "high",
  "medium",
  "low",
  "info",
];

const SOURCES: Array<FindingSource | "all"> = ["all", "static", "organization_policy", "llm"];

export function FindingsFilters({ value, onChange, counts }: FindingsFiltersProps) {
  return (
    <FilterBar
      actions={
        counts ? (
          <p className="text-muted-foreground text-xs">
            Showing {counts.visible} of {counts.total}
          </p>
        ) : null
      }
    >
      <div className="space-y-1">
        <Label className="text-xs">Severity</Label>
        <Select
          value={value.severity}
          onValueChange={(severity) =>
            onChange({
              ...value,
              severity: severity as FindingsFiltersValue["severity"],
            })
          }
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SEVERITIES.map((severity) => (
              <SelectItem key={severity} value={severity}>
                {severity === "all" ? "All severities" : severity}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-1">
        <Label className="text-xs">Source</Label>
        <Select
          value={value.source}
          onValueChange={(source) =>
            onChange({
              ...value,
              source: source as FindingsFiltersValue["source"],
            })
          }
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SOURCES.map((source) => (
              <SelectItem key={source} value={source}>
                {source === "all" ? "All sources" : FINDING_SOURCE_LABELS[source]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </FilterBar>
  );
}
