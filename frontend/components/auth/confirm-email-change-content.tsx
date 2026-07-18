"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import * as React from "react";

import { ErrorState } from "@/components/feedback/error-state";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { confirmEmailChange } from "@/features/auth/api";
import { isApiClientError } from "@/lib/api/errors";

type ConfirmationStatus = "idle" | "loading" | "success" | "error";

export function ConfirmEmailChangeContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token")?.trim() ?? "";
  const [status, setStatus] = React.useState<ConfirmationStatus>(token ? "loading" : "idle");
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const attemptedToken = React.useRef<string | null>(null);

  const confirm = React.useCallback(async () => {
    if (!token || attemptedToken.current === token) {
      return;
    }
    attemptedToken.current = token;
    setStatus("loading");
    setErrorMessage(null);
    try {
      await confirmEmailChange(token);
      setStatus("success");
    } catch (error) {
      setStatus("error");
      setErrorMessage(
        isApiClientError(error)
          ? error.message
          : "Unable to confirm your email change. The link may be invalid or expired.",
      );
    }
  }, [token]);

  React.useEffect(() => {
    void confirm();
  }, [confirm]);

  if (!token) {
    return (
      <ErrorState
        title="Invalid confirmation link"
        message="This email change link is missing a confirmation token."
      />
    );
  }

  if (status === "loading") {
    return (
      <div className="flex flex-col items-center gap-3 py-8">
        <Spinner />
        <p className="text-muted-foreground text-sm">Confirming your new email address…</p>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="space-y-4" role="status">
        <p className="text-sm">Your email address has been changed successfully.</p>
        <Button asChild className="w-full">
          <Link href="/login">Continue to sign in</Link>
        </Button>
      </div>
    );
  }

  return (
    <ErrorState
      title="Email change confirmation failed"
      message={errorMessage ?? "Unable to confirm your email change."}
      onRetry={() => {
        attemptedToken.current = null;
        void confirm();
      }}
    />
  );
}
