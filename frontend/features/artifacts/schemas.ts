import { z } from "zod";

import { ARTIFACT_TYPES, type ArtifactType } from "./constants";

const artifactTypeEnum = ARTIFACT_TYPES as unknown as [ArtifactType, ...ArtifactType[]];

export const artifactCreateSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(200),
  description: z.string().trim().max(2000).optional().or(z.literal("")),
  artifact_type: z.enum(artifactTypeEnum),
  content: z.string().min(1, "Content is required"),
});

export type ArtifactCreateFormValues = z.infer<typeof artifactCreateSchema>;

export const artifactUpdateSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(200),
  description: z.string().trim().max(2000).optional().or(z.literal("")),
});

export type ArtifactUpdateFormValues = z.infer<typeof artifactUpdateSchema>;

export const artifactVersionSchema = z.object({
  content: z.string().min(1, "Content is required"),
});

export type ArtifactVersionFormValues = z.infer<typeof artifactVersionSchema>;
