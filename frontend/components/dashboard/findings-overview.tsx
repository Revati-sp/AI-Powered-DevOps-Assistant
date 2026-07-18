import Link from "next/link";
import { ShieldAlert } from "lucide-react";

import { SectionHeader } from "@/components/data-display/section-header";
import { EmptyState } from "@/components/feedback/empty-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  normalizeFindingCounts,
  type DashboardSummary,
} from "@/features/dashboard/api";

const SEVERITY_ORDER = ["critical", "high", "medium", "low"] as const;

export function FindingsOverview({
  counts,
  loading,
}: {
  counts?: DashboardSummary["findings"] | unknown;
  loading?: boolean;
}) {
  const normalized = normalizeFindingCounts(counts);
  const total = normalized
    ? SEVERITY_ORDER.reduce((sum, key) => sum + (normalized[key] ?? 0), 0)
    : 0;

  return (
    <Card className="h-full">
      <CardContent className="space-y-4 p-6">
        <SectionHeader
          title="Findings overview"
          description="Policy and review findings across your workspace"
        />
        {loading ? (
          <Skeleton className="h-40 w-full" />
        ) : total === 0 ? (
          <EmptyState
            className="py-8"
            icon={<ShieldAlert />}
            title="No findings data yet"
            description="Findings appear after you run reviews or policy checks on generated artifacts. Nothing is fabricated here until that data exists."
            action={
              <Button asChild variant="outline" size="sm">
                <Link href="/reviews">Go to reviews</Link>
              </Button>
            }
          />
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {SEVERITY_ORDER.map((severity) => (
              <div key={severity} className="rounded-lg border p-3">
                <p className="text-muted-foreground text-xs capitalize">{severity}</p>
                <p className="text-2xl font-semibold">{normalized?.[severity] ?? 0}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
