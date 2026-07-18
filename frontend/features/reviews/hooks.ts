"use client";

import { useMutation } from "@tanstack/react-query";

import { reviewConfiguration } from "@/features/reviews/api";
import type { ReviewRequest } from "@/features/reviews/types";

export function useReviewConfiguration() {
  return useMutation({
    mutationFn: (body: ReviewRequest) => reviewConfiguration(body),
  });
}
