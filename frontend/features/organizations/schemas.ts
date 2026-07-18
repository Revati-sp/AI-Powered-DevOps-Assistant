import { z } from "zod";

export const orgRoles = ["owner", "admin", "member", "viewer"] as const;

export const organizationFormSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(200),
  slug: z
    .string()
    .trim()
    .max(64)
    .refine(
      (value) => value === "" || /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value),
      "Use lowercase letters, numbers, and hyphens",
    )
    .optional(),
});

export type OrganizationFormValues = z.infer<typeof organizationFormSchema>;

export const addMemberSchema = z.object({
  email: z.string().trim().email("Enter a valid email"),
  role: z.enum(orgRoles),
});

export type AddMemberFormValues = z.infer<typeof addMemberSchema>;

export const updateMemberSchema = z.object({
  role: z.enum(orgRoles),
});

export type UpdateMemberFormValues = z.infer<typeof updateMemberSchema>;

export const inviteMemberSchema = z.object({
  email: z.string().trim().min(1, "Email is required").email("Enter a valid email address"),
  role: z.enum(orgRoles),
});

export type InviteMemberFormValues = z.infer<typeof inviteMemberSchema>;
