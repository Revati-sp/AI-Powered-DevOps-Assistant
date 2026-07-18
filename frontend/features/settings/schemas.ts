import { z } from "zod";

const optionalText = (max: number) =>
  z
    .string()
    .trim()
    .max(max)
    .optional()
    .or(z.literal(""));

export const profileSettingsSchema = z.object({
  display_name: optionalText(100),
  username: z
    .string()
    .trim()
    .min(3, "Username must be at least 3 characters")
    .max(50)
    .regex(/^[a-zA-Z0-9_-]+$/, "Use letters, numbers, underscores, or hyphens"),
  timezone: optionalText(64),
  job_title: optionalText(100),
  avatar_url: z
    .string()
    .trim()
    .url("Enter a valid URL")
    .refine((value) => value.startsWith("https://"), "Avatar URL must use HTTPS")
    .optional()
    .or(z.literal("")),
});

export type ProfileSettingsValues = z.infer<typeof profileSettingsSchema>;
