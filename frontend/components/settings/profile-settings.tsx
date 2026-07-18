"use client";

import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/data-display/page-header";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { fetchProfile } from "@/features/settings/api";
import { queryKeys } from "@/lib/api/query-keys";
import { isApiClientError } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/formatters/date";

export function ProfileSettings() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: queryKeys.auth.currentUser(),
    queryFn: fetchProfile,
  });

  if (isLoading) {
    return <LoadingState label="Loading profile…" />;
  }

  if (isError || !data) {
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load profile"}
        requestId={isApiClientError(error) ? error.requestId : undefined}
        onRetry={() => void refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Profile" description="Your account details from the API (read-only)." />
      <dl className="grid max-w-lg gap-4">
        <div className="space-y-1">
          <dt className="text-muted-foreground text-sm">Username</dt>
          <dd className="text-sm font-medium">{data.username}</dd>
        </div>
        <div className="space-y-1">
          <dt className="text-muted-foreground text-sm">Email</dt>
          <dd className="text-sm font-medium">{data.email}</dd>
        </div>
        <div className="space-y-1">
          <dt className="text-muted-foreground text-sm">Role</dt>
          <dd className="text-sm font-medium capitalize">{data.role}</dd>
        </div>
        <div className="space-y-1">
          <dt className="text-muted-foreground text-sm">Status</dt>
          <dd className="text-sm font-medium">{data.is_active ? "Active" : "Inactive"}</dd>
        </div>
        <div className="space-y-1">
          <dt className="text-muted-foreground text-sm">Member since</dt>
          <dd className="text-sm font-medium">{formatDateTime(data.created_at)}</dd>
        </div>
      </dl>
    </div>
  );
}
