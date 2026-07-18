import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";

export type Severity = "info" | "low" | "medium" | "high" | "critical";

const severityConfig: Record<Severity, { label: string; className: string }> = {
  info: {
    label: "Info",
    className: "border-transparent bg-info text-info-foreground",
  },
  low: {
    label: "Low",
    className: "border-transparent bg-secondary text-secondary-foreground",
  },
  medium: {
    label: "Medium",
    className: "border-transparent bg-warning text-warning-foreground",
  },
  high: {
    label: "High",
    className: "border-transparent bg-danger/90 text-danger-foreground",
  },
  critical: {
    label: "Critical",
    className: "border-transparent bg-destructive text-destructive-foreground",
  },
};

export interface SeverityBadgeProps {
  severity: Severity;
  className?: string;
}

function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const config = severityConfig[severity];
  return <Badge className={cn(config.className, className)}>{config.label}</Badge>;
}

export { SeverityBadge };
