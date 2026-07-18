import type { components } from "@/lib/api/generated-types";

export type ArtifactType = components["schemas"]["ArtifactType"];
export type ArtifactSummaryResponse = components["schemas"]["ArtifactSummaryResponse"];
export type ArtifactDetailResponse = components["schemas"]["ArtifactDetailResponse"];
export type ArtifactCreateRequest = components["schemas"]["ArtifactCreateRequest"];
export type ArtifactUpdateRequest = components["schemas"]["ArtifactUpdateRequest"];
export type ArtifactVersionResponse = components["schemas"]["ArtifactVersionResponse"];
export type ArtifactVersionCreateRequest = components["schemas"]["ArtifactVersionCreateRequest"];
export type ArtifactDiffResponse = components["schemas"]["ArtifactDiffResponse"];
export type ArtifactRestoreResponse = components["schemas"]["ArtifactRestoreResponse"];
export type ArtifactsPage = components["schemas"]["Page_ArtifactSummaryResponse_"];
export type VersionsPage = components["schemas"]["Page_ArtifactVersionResponse_"];
