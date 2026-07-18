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
  const used = typeof usage?.requests_used === "number" ? usage.requests_used : null;
  const limit = typeof usage?.requests_limit === "number" ? usage.requests_limit : null;
  if (used === null || limit === null) {
    return null;
  }

  const percentage =
    limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;

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
        {used.toLocaleString()} of {limit.toLocaleString()} requests used
      </p>
    </section>
  );
}
