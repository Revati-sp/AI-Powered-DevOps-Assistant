import type { Metadata } from "next";
import { Suspense } from "react";

import { InvitationAcceptContent } from "@/components/organizations/invitation-accept-content";
import { Spinner } from "@/components/ui/spinner";

export const metadata: Metadata = {
  title: "Organization invitation",
};

export default function InvitationAcceptPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-foreground text-2xl font-semibold tracking-tight">
          Organization invitation
        </h1>
        <p className="text-muted-foreground text-sm">
          Accept to join the team or decline to dismiss this invitation.
        </p>
      </div>

      <Suspense
        fallback={
          <div className="flex justify-center py-12">
            <Spinner />
          </div>
        }
      >
        <InvitationAcceptContent />
      </Suspense>
    </div>
  );
}
