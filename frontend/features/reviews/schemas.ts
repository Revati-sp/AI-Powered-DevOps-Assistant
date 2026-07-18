import { z } from "zod";

import { LLM_PROVIDERS } from "@/lib/constants/app";

export const reviewTypeSchema = z.enum([
  "dockerfile",
  "kubernetes",
  "terraform",
  "github-actions",
  "gitlab-ci",
  "jenkins",
]);

export const reviewFormSchema = z.object({
  type: reviewTypeSchema,
  content: z
    .string()
    .min(1, "Configuration content is required")
    .max(500_000, "Content is too large"),
  provider: z.enum(LLM_PROVIDERS),
  organization_id: z.string().uuid().optional().nullable(),
  policy_pack_ids: z.array(z.string().uuid()),
});

export type ReviewFormValues = z.infer<typeof reviewFormSchema>;
