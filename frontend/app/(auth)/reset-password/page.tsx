import { Suspense } from "react";

import { ResetPasswordPageClient } from "@/components/auth/reset-password-page-client";
import { Spinner } from "@/components/ui/spinner";

export default function ResetPasswordPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-foreground text-2xl font-semibold tracking-tight">Reset password</h1>
        <p className="text-muted-foreground text-sm">Choose a new password for your account.</p>
      </div>

      <Suspense
        fallback={
          <div className="flex justify-center py-12">
            <Spinner />
          </div>
        }
      >
        <ResetPasswordPageClient />
      </Suspense>
    </div>
  );
}
