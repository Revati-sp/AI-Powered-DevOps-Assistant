import type { Metadata } from "next";
import { Suspense } from "react";

import { ConfirmEmailChangeContent } from "@/components/auth/confirm-email-change-content";
import { Spinner } from "@/components/ui/spinner";

export const metadata: Metadata = {
  title: "Confirm email change",
};

export default function ConfirmEmailChangePage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-foreground text-2xl font-semibold tracking-tight">
          Confirm email change
        </h1>
        <p className="text-muted-foreground text-sm">
          Confirm the new email address requested for your account.
        </p>
      </div>

      <Suspense fallback={<div className="flex justify-center py-12"><Spinner /></div>}>
        <ConfirmEmailChangeContent />
      </Suspense>
    </div>
  );
}
