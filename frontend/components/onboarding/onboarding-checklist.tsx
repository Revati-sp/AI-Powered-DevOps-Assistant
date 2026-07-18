"use client";

import { Check, Circle, ExternalLink } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

import { SectionHeader } from "@/components/data-display/section-header";
import { LoadingState } from "@/components/feedback/loading-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useOnboarding, usePatchOnboarding } from "@/features/onboarding/hooks";
import {
  computeOnboardingProgress,
  isChecklistItemDone,
  ONBOARDING_CHECKLIST_ITEMS,
} from "@/features/onboarding/progress";
import type { OnboardingChecklistKey } from "@/features/onboarding/types";
import { isApiClientError } from "@/lib/api/errors";
import { cn } from "@/lib/utils/cn";
import { useWorkspaceStore } from "@/store/workspace-store";

type OnboardingChecklistProps = {
  showCompleteAction?: boolean;
  className?: string;
};

export function OnboardingChecklist({
  showCompleteAction = true,
  className,
}: OnboardingChecklistProps) {
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const { data, isLoading } = useOnboarding();
  const patchMutation = usePatchOnboarding();
  const progress = computeOnboardingProgress(data);

  const resolveHref = (href: string, key: OnboardingChecklistKey) => {
    if (key === "invite_team_completed" && organizationId) {
      return `/organizations/${organizationId}/members`;
    }
    return href;
  };

  const markComplete = async (key: OnboardingChecklistKey) => {
    try {
      await patchMutation.mutateAsync({ [key]: true });
      toast.success("Progress saved");
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to update progress");
    }
  };

  const markOnboardingComplete = async () => {
    try {
      await patchMutation.mutateAsync({ onboarding_completed: true, tour_completed: true });
      toast.success("Onboarding marked complete");
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to complete onboarding");
    }
  };

  if (isLoading) {
    return <LoadingState label="Loading checklist…" />;
  }

  return (
    <div className={cn("space-y-4", className)}>
      <SectionHeader
        title="Getting started checklist"
        description={`${progress.completed} of ${progress.total} steps complete`}
        actions={
          showCompleteAction && !data?.onboarding_completed ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={patchMutation.isPending}
              onClick={() => void markOnboardingComplete()}
            >
              Mark all complete
            </Button>
          ) : null
        }
      />

      <Progress value={progress.percent} aria-label="Onboarding progress" />

      <ul className="space-y-3">
        {ONBOARDING_CHECKLIST_ITEMS.map((item) => {
          const done = isChecklistItemDone(data, item.key);
          const href = resolveHref(item.href, item.key);

          return (
            <li key={item.key}>
              <Card className={cn(done && "border-primary/30 bg-primary/5")}>
                <CardHeader className="pb-2">
                  <div className="flex items-start gap-3">
                    <span
                      className={cn(
                        "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border",
                        done ? "bg-primary text-primary-foreground border-primary" : "bg-muted",
                      )}
                      aria-hidden
                    >
                      {done ? <Check className="h-3.5 w-3.5" /> : <Circle className="h-3.5 w-3.5" />}
                    </span>
                    <div className="min-w-0 flex-1 space-y-1">
                      <CardTitle className="text-base">{item.label}</CardTitle>
                      <CardDescription>{item.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2 pt-0">
                  <Button type="button" variant="outline" size="sm" asChild>
                    <Link href={href}>
                      Open
                      <ExternalLink className="h-3.5 w-3.5" />
                    </Link>
                  </Button>
                  {!done ? (
                    <Button
                      type="button"
                      size="sm"
                      disabled={patchMutation.isPending}
                      onClick={() => void markComplete(item.key)}
                    >
                      Mark done
                    </Button>
                  ) : null}
                </CardContent>
              </Card>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
