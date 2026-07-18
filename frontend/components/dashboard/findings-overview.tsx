import Link from "next/link";
import { ShieldAlert } from "lucide-react";

import { SectionHeader } from "@/components/data-display/section-header";
import { EmptyState } from "@/components/feedback/empty-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function FindingsOverview() {
  return (
    <Card className="h-full">
      <CardContent className="space-y-4 p-6">
        <SectionHeader
          title="Findings overview"
          description="Policy and review findings across your workspace"
        />
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
      </CardContent>
    </Card>
  );
}
