"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Monitor } from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { PageHeader } from "@/components/data-display/page-header";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { PasswordInput } from "@/components/ui/password-input";
import { logoutAllRequest, logoutRequest } from "@/features/auth/api";
import { useChangePassword, useRevokeSession, useSessions } from "@/features/auth/hooks";
import { changePasswordSchema, type ChangePasswordFormValues } from "@/features/auth/schemas";
import type { SessionResponse } from "@/features/auth/types";
import { isApiClientError } from "@/lib/api/errors";
import { formatDateTime, formatRelative } from "@/lib/formatters/date";
import { PASSWORD_MIN } from "@/lib/constants/app";
import { useAuth } from "@/hooks/use-auth";

export function SecuritySettings() {
  const router = useRouter();
  const { refreshUser } = useAuth();
  const [logoutOpen, setLogoutOpen] = React.useState(false);
  const [logoutAllOpen, setLogoutAllOpen] = React.useState(false);
  const [pendingRevoke, setPendingRevoke] = React.useState<SessionResponse | null>(null);
  const [authActionLoading, setAuthActionLoading] = React.useState(false);

  const {
    data: sessions,
    isLoading: sessionsLoading,
    isError: sessionsError,
    error: sessionsQueryError,
    refetch: refetchSessions,
  } = useSessions();
  const revokeMutation = useRevokeSession();
  const changePasswordMutation = useChangePassword();

  const passwordForm = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  });

  const handleLogout = async () => {
    setAuthActionLoading(true);
    try {
      await logoutRequest();
      await refreshUser();
      toast.success("Signed out");
      router.replace("/login");
      router.refresh();
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to sign out");
    } finally {
      setAuthActionLoading(false);
      setLogoutOpen(false);
    }
  };

  const handleLogoutAll = async () => {
    setAuthActionLoading(true);
    try {
      await logoutAllRequest();
      await refreshUser();
      toast.success("Signed out of all sessions");
      router.replace("/login");
      router.refresh();
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to sign out everywhere");
    } finally {
      setAuthActionLoading(false);
      setLogoutAllOpen(false);
    }
  };

  const handleChangePassword = passwordForm.handleSubmit(async (values) => {
    try {
      await changePasswordMutation.mutateAsync({
        current_password: values.current_password,
        new_password: values.new_password,
      });
      passwordForm.reset();
      toast.success("Password updated");
      void refetchSessions();
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to change password");
    }
  });

  const confirmRevokeSession = async () => {
    if (!pendingRevoke) {
      return;
    }
    try {
      await revokeMutation.mutateAsync(pendingRevoke.id);
      toast.success(
        pendingRevoke.is_current ? "Current session revoked" : "Session revoked",
      );
      if (pendingRevoke.is_current) {
        await refreshUser();
        router.replace("/login");
        router.refresh();
      }
      setPendingRevoke(null);
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to revoke session");
    }
  };

  const activeSessions = (sessions ?? []).filter((session) => !session.revoked);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Security"
        description="Manage your password, active sessions, and sign-in status."
      />

      <section className="max-w-lg space-y-4" aria-labelledby="change-password-heading">
        <div className="space-y-1">
          <h2 id="change-password-heading" className="text-sm font-medium">
            Change password
          </h2>
          <p className="text-muted-foreground text-xs">
            Other sessions may be signed out after a password change.
          </p>
        </div>

        <Form {...passwordForm}>
          <form onSubmit={handleChangePassword} className="space-y-4 rounded-md border p-4">
            <FormField
              control={passwordForm.control}
              name="current_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Current password</FormLabel>
                  <FormControl>
                    <PasswordInput
                      autoComplete="current-password"
                      disabled={changePasswordMutation.isPending}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={passwordForm.control}
              name="new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>New password</FormLabel>
                  <FormControl>
                    <PasswordInput
                      autoComplete="new-password"
                      disabled={changePasswordMutation.isPending}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>At least {PASSWORD_MIN} characters.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={passwordForm.control}
              name="confirm_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirm new password</FormLabel>
                  <FormControl>
                    <PasswordInput
                      autoComplete="new-password"
                      disabled={changePasswordMutation.isPending}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" disabled={changePasswordMutation.isPending}>
              {changePasswordMutation.isPending ? "Updating…" : "Update password"}
            </Button>
          </form>
        </Form>
      </section>

      <section className="space-y-4" aria-labelledby="sessions-heading">
        <div className="space-y-1">
          <h2 id="sessions-heading" className="text-sm font-medium">
            Active sessions
          </h2>
          <p className="text-muted-foreground text-xs">
            Devices and browsers currently signed in to your account.
          </p>
        </div>

        {sessionsLoading ? <LoadingState label="Loading sessions…" /> : null}

        {sessionsError ? (
          <ErrorState
            message={
              isApiClientError(sessionsQueryError)
                ? sessionsQueryError.message
                : "Failed to load sessions"
            }
            requestId={
              isApiClientError(sessionsQueryError) ? sessionsQueryError.requestId : undefined
            }
            onRetry={() => void refetchSessions()}
          />
        ) : null}

        {!sessionsLoading && !sessionsError && activeSessions.length === 0 ? (
          <EmptyState
            icon={<Monitor aria-hidden />}
            title="No active sessions"
            description="You are not signed in on any devices."
          />
        ) : null}

        {!sessionsLoading && !sessionsError && activeSessions.length > 0 ? (
          <ul className="divide-border divide-y rounded-md border">
            {activeSessions.map((session) => (
              <li
                key={session.id}
                className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium">
                      {session.approx_client ?? "Unknown device"}
                    </span>
                    {session.is_current ? <Badge variant="success">Current</Badge> : null}
                    {session.revoked ? <Badge variant="secondary">Revoked</Badge> : null}
                  </div>
                  <p className="text-muted-foreground text-xs">
                    {session.approx_ip ? `Approx. IP ${session.approx_ip} · ` : null}
                    Signed in {formatRelative(session.created_at)} · Expires{" "}
                    {formatDateTime(session.expires_at)}
                  </p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={revokeMutation.isPending}
                  onClick={() => setPendingRevoke(session)}
                >
                  Revoke
                </Button>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="max-w-lg space-y-4" aria-labelledby="sign-out-heading">
        <div className="space-y-1">
          <h2 id="sign-out-heading" className="text-sm font-medium">
            Sign out
          </h2>
          <p className="text-muted-foreground text-xs">
            End sessions on this device or everywhere.
          </p>
        </div>

        <div className="flex flex-col gap-3 rounded-md border p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-sm font-medium">Sign out</h3>
            <p className="text-muted-foreground text-xs">End the current browser session.</p>
          </div>
          <Button type="button" variant="outline" onClick={() => setLogoutOpen(true)}>
            Sign out
          </Button>
        </div>

        <div className="flex flex-col gap-3 rounded-md border p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-sm font-medium">Sign out everywhere</h3>
            <p className="text-muted-foreground text-xs">
              Revoke all refresh tokens across devices.
            </p>
          </div>
          <Button type="button" variant="destructive" onClick={() => setLogoutAllOpen(true)}>
            Sign out all
          </Button>
        </div>
      </section>

      <ConfirmationDialog
        open={Boolean(pendingRevoke)}
        onOpenChange={(open) => {
          if (!open) {
            setPendingRevoke(null);
          }
        }}
        title={pendingRevoke?.is_current ? "Revoke current session?" : "Revoke session?"}
        description={
          pendingRevoke?.is_current
            ? "You will be signed out of this browser immediately."
            : "This device will need to sign in again."
        }
        confirmLabel="Revoke"
        variant={pendingRevoke?.is_current ? "destructive" : "default"}
        loading={revokeMutation.isPending}
        onConfirm={() => void confirmRevokeSession()}
      />

      <ConfirmationDialog
        open={logoutOpen}
        onOpenChange={setLogoutOpen}
        title="Sign out?"
        description="You will need to sign in again to continue."
        confirmLabel="Sign out"
        loading={authActionLoading}
        onConfirm={() => void handleLogout()}
      />

      <ConfirmationDialog
        open={logoutAllOpen}
        onOpenChange={setLogoutAllOpen}
        title="Sign out of all sessions?"
        description="This revokes access on every device using your account."
        confirmLabel="Sign out all"
        variant="destructive"
        loading={authActionLoading}
        onConfirm={() => void handleLogoutAll()}
      />
    </div>
  );
}
