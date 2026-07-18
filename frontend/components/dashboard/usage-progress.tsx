import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import type { DashboardSnapshot } from "@/features/dashboard/api";

export function UsageProgress({
  snapshot,
  loading,
}: {
  snapshot?: DashboardSnapshot;
  loading?: boolean;
}) {
  if (loading) {
    return <Skeleton className="h-28 w-full" />;
  }

  const usage = snapshot?.summary?.usage;
  if (!usage) {
    return null;
  }

  const percentage =
    usage.requests_limit > 0
      ? Math.min(100, Math.round((usage.requests_used / usage.requests_limit) * 100))
      : 0;

  return (
    <section className="space-y-3 rounded-lg border p-4" aria-label="Request usage">
      <div className="flex items-baseline justify-between gap-4">
        <div>
          <h2 className="text-sm font-medium">Request usage</h2>
          <p className="text-muted-foreground text-xs">Current plan usage</p>
        </div>
        <span className="text-sm font-medium">{percentage}%</span>
      </div>
      <Progress value={percentage} aria-label={`${percentage}% of request limit used`} />
      <p className="text-muted-foreground text-xs">
        {usage.requests_used.toLocaleString()} of {usage.requests_limit.toLocaleString()} requests used
      </p>
    </section>
  );
}
