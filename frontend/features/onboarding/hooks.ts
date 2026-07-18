"use client";

import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from "@tanstack/react-query";

import { queryKeys } from "@/lib/api/query-keys";

import { fetchOnboarding, patchOnboarding } from "./api";
import type { UserOnboardingPatchRequest, UserOnboardingResponse } from "./types";

export function useOnboarding(
  options?: Omit<UseQueryOptions<UserOnboardingResponse>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.onboarding.me(),
    queryFn: fetchOnboarding,
    ...options,
  });
}

export function usePatchOnboarding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UserOnboardingPatchRequest) => patchOnboarding(body),
    onMutate: async (body) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.onboarding.me() });
      const previous = queryClient.getQueryData<UserOnboardingResponse>(
        queryKeys.onboarding.me(),
      );
      if (previous) {
        queryClient.setQueryData<UserOnboardingResponse>(queryKeys.onboarding.me(), {
          ...previous,
          ...body,
        });
      }
      return { previous };
    },
    onError: (_err, _body, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.onboarding.me(), context.previous);
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.onboarding.me() });
    },
  });
}
