"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { Button } from "@/components/ui/button";
import {
  acceptInvitationRequest,
  declineInvitationRequest,
} from "@/features/auth/api";
import { isApiClientError } from "@/lib/api/errors";
import { getSafeReturnUrl } from "@/lib/utils/return-url";
import { useAuth } from "@/hooks/use-auth";

export function InvitationAcceptContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token")?.trim() ?? "";
  const { user, isLoading: authLoading } = useAuth();
  const [loadingAction, setLoadingAction] = React.useState<"accept" | "decline" | null>(null);
  const [acceptedOrg, setAcceptedOrg] = React.useState<string | null>(null);
  const [declined, setDeclined] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const returnUrl = getSafeReturnUrl(
    token ? `/invitations/accept?token=${encodeURIComponent(token)}` : "/invitations/accept",
  );

  const handleAccept = async () => {
    if (!token) {
      return;
    }
    setLoadingAction("accept");
    setErrorMessage(null);
    try {
      const result = await acceptInvitationRequest(token);
      setAcceptedOrg(result.organization_name);
      toast.success(`Joined ${result.organization_name}`);
    } catch (error) {
      setErrorMessage(
        isApiClientError(error) ? error.message : "Unable to accept this invitation.",
      );
    } finally {
      setLoadingAction(null);
    }
  };

  const handleDecline = async () => {
    if (!token) {
      return;
    }
    setLoadingAction("decline");
    setErrorMessage(null);
    try {
      await declineInvitationRequest(token);
      setDeclined(true);
      toast.success("Invitation declined");
    } catch (error) {
      setErrorMessage(
        isApiClientError(error) ? error.message : "Unable to decline this invitation.",
      );
    } finally {
      setLoadingAction(null);
    }
  };

  if (!token) {
    return (
      <ErrorState
        title="Missing invitation token"
        message="This invitation link is incomplete. Open the link from your email or ask the sender to resend it."
      />
    );
  }

  if (authLoading) {
    return <LoadingState label="Loading…" />;
  }

  if (acceptedOrg) {
    return (
      <div className="space-y-4" role="status">
        <p className="text-sm">
          You are now a member of <span className="font-medium">{acceptedOrg}</span>.
        </p>
        <Button className="w-full" onClick={() => router.push("/organizations")}>
          View organizations
        </Button>
      </div>
    );
  }

  if (declined) {
    return (
      <div className="space-y-4" role="status">
        <p className="text-sm">You declined this organization invitation.</p>
        <Button asChild variant="outline" className="w-full">
          <Link href={user ? "/dashboard" : "/login"}>{user ? "Go to dashboard" : "Sign in"}</Link>
        </Button>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="space-y-4">
        <p className="text-muted-foreground text-sm">
          Sign in with the email address that received this invitation to accept or decline it.
        </p>
        <Button asChild className="w-full">
          <Link href={`/login?returnUrl=${encodeURIComponent(returnUrl)}`}>Sign in to continue</Link>
        </Button>
        <Button
          type="button"
          variant="outline"
          className="w-full"
          disabled={loadingAction === "decline"}
          onClick={() => void handleDecline()}
        >
          {loadingAction === "decline" ? "Declining…" : "Decline without signing in"}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <p className="text-muted-foreground text-sm">
        Signed in as <span className="text-foreground font-medium">{user.email}</span>. Accept to
        join the organization or decline to dismiss this invitation.
      </p>

      {errorMessage ? (
        <p
          role="alert"
          className="bg-destructive/10 text-destructive rounded-md px-3 py-2 text-sm"
        >
          {errorMessage}
        </p>
      ) : null}

      <div className="flex flex-col gap-3 sm:flex-row">
        <Button
          type="button"
          className="flex-1"
          disabled={loadingAction !== null}
          onClick={() => void handleAccept()}
        >
          {loadingAction === "accept" ? "Accepting…" : "Accept invitation"}
        </Button>
        <Button
          type="button"
          variant="outline"
          className="flex-1"
          disabled={loadingAction !== null}
          onClick={() => void handleDecline()}
        >
          {loadingAction === "decline" ? "Declining…" : "Decline"}
        </Button>
      </div>
    </div>
  );
}
