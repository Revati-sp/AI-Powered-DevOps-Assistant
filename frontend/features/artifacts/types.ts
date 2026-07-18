import type { components } from "@/lib/api/generated-types";

export type ArtifactType = components["schemas"]["ArtifactType"];

/** Extends generated summary with productization fields that may lag in openapi.json. */
export type ArtifactSummaryResponse = components["schemas"]["ArtifactSummaryResponse"] & {
  archived_at?: string | null;
  is_favorited?: boolean;
  tags?: string[];
};

export type ArtifactDetailResponse = components["schemas"]["ArtifactDetailResponse"] & {
  archived_at?: string | null;
  is_favorited?: boolean;
  tags?: string[];
};

export type ArtifactCreateRequest = components["schemas"]["ArtifactCreateRequest"];
export type ArtifactUpdateRequest = components["schemas"]["ArtifactUpdateRequest"];
export type ArtifactVersionResponse = components["schemas"]["ArtifactVersionResponse"];
export type ArtifactVersionCreateRequest = components["schemas"]["ArtifactVersionCreateRequest"];
export type ArtifactDiffResponse = components["schemas"]["ArtifactDiffResponse"];
export type ArtifactRestoreResponse = components["schemas"]["ArtifactRestoreResponse"];
export type ArtifactsPage = components["schemas"]["Page_ArtifactSummaryResponse_"] & {
  items: ArtifactSummaryResponse[];
};
export type VersionsPage = components["schemas"]["Page_ArtifactVersionResponse_"];

export type ArtifactTagResponse = {
  id: string;
  organization_id: string | null;
  user_id: string;
  name: string;
  color: string | null;
  created_at: string;
};

export type ArtifactTagCreateRequest = {
  name: string;
  color?: string | null;
};

export type ArtifactTagAssignRequest = {
  tag_id?: string;
  name?: string;
  color?: string | null;
};
