import Link from "next/link";
import { Activity } from "lucide-react";

import { SectionHeader } from "@/components/data-display/section-header";
import { EmptyState } from "@/components/feedback/empty-state";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { DashboardActivityItem } from "@/features/dashboard/api";
import { formatRelative } from "@/lib/formatters/date";

export function RecentActivity({
  items,
  loading,
}: {
  items: DashboardActivityItem[];
  loading?: boolean;
}) {
  return (
    <Card className="h-full">
      <CardContent className="space-y-4 p-6">
        <SectionHeader
          title="Recent activity"
          description="Latest conversations, artifacts, and tasks"
        />

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-12 w-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            className="py-8"
            icon={<Activity />}
            title="No recent activity"
            description="Start a chat, generate an artifact, or run a task to populate this feed."
          />
        ) : (
          <ul className="space-y-2">
            {items.map((item) => (
              <li key={item.id}>
                <Link
                  href={item.href}
                  className="hover:bg-primary/5 border-border flex items-start justify-between gap-3 rounded-lg border px-3 py-2.5 transition-colors"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{item.title}</p>
                    <p className="text-muted-foreground truncate text-xs">{item.subtitle}</p>
                  </div>
                  <time className="text-muted-foreground shrink-0 text-xs" dateTime={item.at}>
                    {formatRelative(item.at)}
                  </time>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
