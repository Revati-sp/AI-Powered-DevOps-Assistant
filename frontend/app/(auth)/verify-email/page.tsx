import type { Metadata } from "next";
import { Suspense } from "react";

import { VerifyEmailContent } from "@/components/auth/verify-email-content";
import { Spinner } from "@/components/ui/spinner";

export const metadata: Metadata = {
  title: "Verify email",
};

export default function VerifyEmailPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-foreground text-2xl font-semibold tracking-tight">Verify email</h1>
        <p className="text-muted-foreground text-sm">
          Confirm your email address or request a new verification link.
        </p>
      </div>

      <Suspense
        fallback={
          <div className="flex justify-center py-12">
            <Spinner />
          </div>
        }
      >
        <VerifyEmailContent />
      </Suspense>
    </div>
  );
}
