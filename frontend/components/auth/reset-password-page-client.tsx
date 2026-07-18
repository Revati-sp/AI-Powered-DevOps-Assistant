"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { ResetPasswordForm } from "@/components/auth/reset-password-form";
import { ErrorState } from "@/components/feedback/error-state";
import { Button } from "@/components/ui/button";

export function ResetPasswordPageClient() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token")?.trim() ?? "";

  if (!token) {
    return (
      <div className="space-y-4">
        <ErrorState
          title="Invalid reset link"
          message="This password reset link is missing a token. Request a new link from the forgot password page."
        />
        <Button asChild variant="outline" className="w-full">
          <Link href="/forgot-password">Request a new link</Link>
        </Button>
      </div>
    );
  }

  return <ResetPasswordForm token={token} />;
}
