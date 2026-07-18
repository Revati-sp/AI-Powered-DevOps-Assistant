import { z } from "zod";

import { PASSWORD_MAX, PASSWORD_MIN } from "@/lib/constants/app";

export const loginSchema = z.object({
  username: z.string().trim().min(1, "Username is required").max(100, "Username is too long"),
  password: z.string().min(1, "Password is required"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  email: z.string().trim().min(1, "Email is required").email("Enter a valid email address"),
  username: z
    .string()
    .trim()
    .min(3, "Username must be at least 3 characters")
    .max(100, "Username must be at most 100 characters")
    .regex(
      /^[a-zA-Z0-9_\-.]+$/,
      "Username may only contain letters, numbers, underscores, hyphens, and dots",
    ),
  password: z
    .string()
    .min(PASSWORD_MIN, `Password must be at least ${PASSWORD_MIN} characters`)
    .max(PASSWORD_MAX, `Password must be at most ${PASSWORD_MAX} characters`),
});

export type RegisterFormValues = z.infer<typeof registerSchema>;
