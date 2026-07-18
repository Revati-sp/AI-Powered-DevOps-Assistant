"use client";

import { useRouter } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/data-display/page-header";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";
import { Button } from "@/components/ui/button";
import { logoutAllRequest, logoutRequest } from "@/features/auth/api";
import { isApiClientError } from "@/lib/api/errors";
import { useAuth } from "@/hooks/use-auth";

export function SecuritySettings() {
  const router = useRouter();
  const { refreshUser } = useAuth();
  const [logoutOpen, setLogoutOpen] = React.useState(false);
  const [logoutAllOpen, setLogoutAllOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  const handleLogout = async () => {
    setLoading(true);
    try {
      await logoutRequest();
      await refreshUser();
      toast.success("Signed out");
      router.replace("/login");
      router.refresh();
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to sign out");
    } finally {
      setLoading(false);
      setLogoutOpen(false);
    }
  };

  const handleLogoutAll = async () => {
    setLoading(true);
    try {
      await logoutAllRequest();
      await refreshUser();
      toast.success("Signed out of all sessions");
      router.replace("/login");
      router.refresh();
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to sign out everywhere");
    } finally {
      setLoading(false);
      setLogoutAllOpen(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Security" description="Manage your signed-in sessions." />

      <div className="max-w-lg space-y-4">
        <div className="flex flex-col gap-3 rounded-md border p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-sm font-medium">Sign out</h2>
            <p className="text-muted-foreground text-xs">End the current browser session.</p>
          </div>
          <Button type="button" variant="outline" onClick={() => setLogoutOpen(true)}>
            Sign out
          </Button>
        </div>

        <div className="flex flex-col gap-3 rounded-md border p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-sm font-medium">Sign out everywhere</h2>
            <p className="text-muted-foreground text-xs">
              Revoke all refresh tokens across devices.
            </p>
          </div>
          <Button type="button" variant="destructive" onClick={() => setLogoutAllOpen(true)}>
            Sign out all
          </Button>
        </div>
      </div>

      <ConfirmationDialog
        open={logoutOpen}
        onOpenChange={setLogoutOpen}
        title="Sign out?"
        description="You will need to sign in again to continue."
        confirmLabel="Sign out"
        loading={loading}
        onConfirm={() => void handleLogout()}
      />

      <ConfirmationDialog
        open={logoutAllOpen}
        onOpenChange={setLogoutAllOpen}
        title="Sign out of all sessions?"
        description="This revokes access on every device using your account."
        confirmLabel="Sign out all"
        variant="destructive"
        loading={loading}
        onConfirm={() => void handleLogoutAll()}
      />
    </div>
  );
}
