import { z } from "zod";

import { CHAT_MESSAGE_MAX, LLM_PROVIDERS } from "@/lib/constants/app";

export const chatComposerSchema = z.object({
  message: z
    .string()
    .trim()
    .min(1, "Message is required")
    .max(CHAT_MESSAGE_MAX, `Message must be at most ${CHAT_MESSAGE_MAX} characters`),
  provider: z.enum(LLM_PROVIDERS),
});

export type ChatComposerSchemaValues = z.infer<typeof chatComposerSchema>;
