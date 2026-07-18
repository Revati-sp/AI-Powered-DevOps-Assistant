"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as React from "react";

import { isApiClientError, shouldRetryStatus } from "@/lib/api/errors";

const NO_RETRY_STATUSES = new Set([401, 403, 404, 409, 422, 429]);

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: (failureCount, error) => {
          if (isApiClientError(error)) {
            if (NO_RETRY_STATUSES.has(error.status)) {
              return false;
            }
            if (shouldRetryStatus(error.status)) {
              return failureCount < 2;
            }
            return false;
          }
          // Network / unknown errors
          return failureCount < 2;
        },
      },
      mutations: {
        retry: false,
      },
    },
  });
}

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = React.useState(makeQueryClient);

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
