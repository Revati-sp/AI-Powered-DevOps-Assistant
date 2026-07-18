"use client";

import Link from "next/link";
import { Building2, Users } from "lucide-react";

import { SectionHeader } from "@/components/data-display/section-header";
import { EmptyState } from "@/components/feedback/empty-state";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { DashboardSnapshot } from "@/features/dashboard/api";
import { useWorkspaceStore } from "@/store/workspace-store";

export function WorkspaceStatus({
  snapshot,
  loading,
}: {
  snapshot?: DashboardSnapshot;
  loading?: boolean;
}) {
  const currentOrganizationId = useWorkspaceStore((state) => state.currentOrganizationId);
  const organization = snapshot?.summary?.organization;

  return (
    <Card className="h-full">
      <CardContent className="space-y-4 p-6">
        <SectionHeader title="Workspace status" description="Current organization context" />

        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-10 w-2/3" />
          </div>
        ) : !organization ? (
          <EmptyState
            className="py-8"
            icon={<Building2 />}
            title="No organization selected"
            description="Create or join an organization to collaborate on policies and shared artifacts."
          />
        ) : (
          <div className="space-y-4">
            <div className="border-border bg-primary/5 rounded-xl border p-4">
              <p className="text-muted-foreground text-xs tracking-wide uppercase">
                Active organization
              </p>
              <p className="mt-1 text-lg font-semibold">Selected workspace</p>
              <p className="text-muted-foreground text-sm">Organization aggregate data</p>
            </div>

            <div className="text-muted-foreground flex items-center gap-2 text-sm">
              <Users className="h-4 w-4" />
              <span>{organization.member_count} members · {organization.active_policy_packs} active policy packs</span>
            </div>

            <Link
              href={currentOrganizationId ? `/organizations/${currentOrganizationId}` : "/organizations"}
              className="text-primary text-sm font-medium hover:underline"
            >
              View organization
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
