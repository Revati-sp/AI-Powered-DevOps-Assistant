import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";

export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

const statusConfig: Record<JobStatus, { label: string; className: string }> = {
  queued: {
    label: "Queued",
    className: "border-transparent bg-secondary text-secondary-foreground",
  },
  running: {
    label: "Running",
    className: "border-transparent bg-info text-info-foreground",
  },
  succeeded: {
    label: "Succeeded",
    className: "border-transparent bg-success text-success-foreground",
  },
  failed: {
    label: "Failed",
    className: "border-transparent bg-danger text-danger-foreground",
  },
  cancelled: {
    label: "Cancelled",
    className: "border-transparent bg-muted text-muted-foreground",
  },
};

export interface StatusBadgeProps {
  status: JobStatus;
  className?: string;
}

function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status];
  return <Badge className={cn(config.className, className)}>{config.label}</Badge>;
}

export { StatusBadge };
