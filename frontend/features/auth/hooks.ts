"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  changePasswordRequest,
  listSessionsRequest,
  revokeSessionRequest,
  sendVerificationRequest,
} from "@/features/auth/api";
import type { ChangePasswordFormValues } from "@/features/auth/schemas";
import { queryKeys } from "@/lib/api/query-keys";

export function useSessions() {
  return useQuery({
    queryKey: queryKeys.auth.sessions(),
    queryFn: listSessionsRequest,
  });
}

export function useRevokeSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => revokeSessionRequest(sessionId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.auth.sessions() });
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (values: Pick<ChangePasswordFormValues, "current_password" | "new_password">) =>
      changePasswordRequest(values),
  });
}

export function useSendVerification() {
  return useMutation({
    mutationFn: sendVerificationRequest,
  });
}
