"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  sendVerificationRequest,
  verifyEmailRequest,
} from "@/features/auth/api";
import { isApiClientError } from "@/lib/api/errors";
import { useAuth } from "@/hooks/use-auth";

type VerifyStatus = "idle" | "loading" | "success" | "error";

export function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token")?.trim() ?? "";
  const { user, isLoading: authLoading, refreshUser } = useAuth();
  const [status, setStatus] = React.useState<VerifyStatus>(token ? "loading" : "idle");
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [resending, setResending] = React.useState(false);
  const attemptedToken = React.useRef<string | null>(null);

  React.useEffect(() => {
    if (!token || attemptedToken.current === token) {
      return;
    }
    attemptedToken.current = token;

    (async () => {
      setStatus("loading");
      setErrorMessage(null);
      try {
        await verifyEmailRequest(token);
        await refreshUser();
        setStatus("success");
      } catch (error) {
        setStatus("error");
        setErrorMessage(
          isApiClientError(error)
            ? error.message
            : "Unable to verify email. The link may be invalid or expired.",
        );
      }
    })();
  }, [token, refreshUser]);

  const handleResend = async () => {
    setResending(true);
    try {
      await sendVerificationRequest();
      toast.success("Verification email sent", {
        description: "Check your inbox for a new link.",
      });
    } catch (error) {
      toast.error(
        isApiClientError(error) ? error.message : "Unable to send verification email.",
      );
    } finally {
      setResending(false);
    }
  };

  if (token && status === "loading") {
    return (
      <div className="flex flex-col items-center gap-3 py-8">
        <Spinner />
        <p className="text-muted-foreground text-sm">Verifying your email…</p>
      </div>
    );
  }

  if (token && status === "success") {
    return (
      <div className="space-y-4" role="status">
        <p className="text-sm">Your email address has been verified.</p>
        <Button
          className="w-full"
          onClick={() => {
            router.push(user ? "/dashboard" : "/login");
          }}
        >
          {user ? "Go to dashboard" : "Continue to sign in"}
        </Button>
      </div>
    );
  }

  if (token && status === "error") {
    return (
      <ErrorState
        title="Verification failed"
        message={errorMessage ?? "Unable to verify your email."}
        onRetry={() => {
          attemptedToken.current = null;
          setStatus("loading");
          void (async () => {
            try {
              await verifyEmailRequest(token);
              await refreshUser();
              setStatus("success");
            } catch (error) {
              setStatus("error");
              setErrorMessage(
                isApiClientError(error)
                  ? error.message
                  : "Unable to verify email. The link may be invalid or expired.",
              );
            }
          })();
        }}
      />
    );
  }

  if (authLoading) {
    return <LoadingState label="Loading…" />;
  }

  if (user) {
    return (
      <div className="space-y-4">
        <p className="text-muted-foreground text-sm">
          Need a new verification link for <span className="text-foreground">{user.email}</span>?
        </p>
        <Button type="button" className="w-full" disabled={resending} onClick={() => void handleResend()}>
          {resending ? "Sending…" : "Resend verification email"}
        </Button>
        <Button asChild variant="outline" className="w-full">
          <Link href="/dashboard">Back to dashboard</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-muted-foreground text-sm">
        Open the verification link from your email, or sign in to request a new one.
      </p>
      <Button asChild className="w-full">
        <Link href="/login">Sign in</Link>
      </Button>
    </div>
  );
}
