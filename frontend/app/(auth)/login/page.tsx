import { Suspense } from "react";

import { LoginForm } from "@/components/auth/login-form";
import { Spinner } from "@/components/ui/spinner";

export default function LoginPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-foreground text-2xl font-semibold tracking-tight">Sign in</h1>
        <p className="text-muted-foreground text-sm">Access your DevOps workspace securely.</p>
      </div>

      <Suspense
        fallback={
          <div className="flex justify-center py-12">
            <Spinner />
          </div>
        }
      >
        <LoginForm />
      </Suspense>
    </div>
  );
}
