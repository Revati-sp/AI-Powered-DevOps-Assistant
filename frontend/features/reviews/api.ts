import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";

import type { ReviewRequest, ReviewResponse } from "@/features/reviews/types";

export function reviewConfiguration(body: ReviewRequest) {
  return apiFetch<ReviewResponse>(endpoints.review(), {
    method: "POST",
    body,
    timeoutMs: 120_000,
  });
}
