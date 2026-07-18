"use client";

import { Sparkles, X } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useOnboarding, usePatchOnboarding } from "@/features/onboarding/hooks";
import { computeOnboardingProgress } from "@/features/onboarding/progress";
import { isApiClientError } from "@/lib/api/errors";

export function WelcomeBanner() {
  const { data, isLoading } = useOnboarding();
  const patchMutation = usePatchOnboarding();
  const progress = computeOnboardingProgress(data);

  if (isLoading || !data || data.welcome_dismissed || data.onboarding_completed) {
    return null;
  }

  const dismiss = async () => {
    try {
      await patchMutation.mutateAsync({ welcome_dismissed: true });
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to dismiss banner");
    }
  };

  return (
    <Card className="border-primary/30 bg-primary/5">
      <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <Sparkles className="text-primary mt-0.5 h-5 w-5 shrink-0" aria-hidden />
          <div className="space-y-1">
            <p className="font-medium">Welcome to AI DevOps Assistant</p>
            <p className="text-muted-foreground text-sm">
              Complete the getting started checklist ({progress.completed}/{progress.total} done) to
              unlock the full workflow — chat, logs, artifacts, and team collaboration.
            </p>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Button type="button" size="sm" asChild>
            <Link href="/onboarding">Get started</Link>
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Dismiss welcome banner"
            disabled={patchMutation.isPending}
            onClick={() => void dismiss()}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
