import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { buildQueryString } from "@/lib/api/query-string";

import type {
  ArtifactCreateRequest,
  ArtifactDetailResponse,
  ArtifactDiffResponse,
  ArtifactRestoreResponse,
  ArtifactsPage,
  ArtifactUpdateRequest,
  ArtifactVersionCreateRequest,
  ArtifactVersionResponse,
  VersionsPage,
} from "./types";

export type ListArtifactsParams = {
  organization_id?: string | null;
  limit?: number;
  offset?: number;
};

export function listArtifacts(params: ListArtifactsParams = {}): Promise<ArtifactsPage> {
  const qs = buildQueryString({
    organization_id: params.organization_id ?? undefined,
    limit: params.limit ?? 20,
    offset: params.offset ?? 0,
  });
  return apiFetch<ArtifactsPage>(`${endpoints.artifacts.list()}${qs}`);
}

export function getArtifact(artifactId: string): Promise<ArtifactDetailResponse> {
  return apiFetch<ArtifactDetailResponse>(endpoints.artifacts.detail(artifactId));
}

export function createArtifact(body: ArtifactCreateRequest): Promise<ArtifactDetailResponse> {
  return apiFetch<ArtifactDetailResponse>(endpoints.artifacts.list(), {
    method: "POST",
    body,
  });
}

export function updateArtifact(
  artifactId: string,
  body: ArtifactUpdateRequest,
): Promise<ArtifactDetailResponse> {
  return apiFetch<ArtifactDetailResponse>(endpoints.artifacts.detail(artifactId), {
    method: "PATCH",
    body,
  });
}

export function deleteArtifact(artifactId: string): Promise<void> {
  return apiFetch<void>(endpoints.artifacts.detail(artifactId), {
    method: "DELETE",
  });
}

export function listVersions(
  artifactId: string,
  params: { limit?: number; offset?: number } = {},
): Promise<VersionsPage> {
  const qs = buildQueryString({
    limit: params.limit ?? 50,
    offset: params.offset ?? 0,
  });
  return apiFetch<VersionsPage>(`${endpoints.artifacts.versions(artifactId)}${qs}`);
}

export function getVersion(
  artifactId: string,
  versionNumber: number,
): Promise<ArtifactVersionResponse> {
  return apiFetch<ArtifactVersionResponse>(endpoints.artifacts.version(artifactId, versionNumber));
}

export function createVersion(
  artifactId: string,
  body: ArtifactVersionCreateRequest,
): Promise<ArtifactVersionResponse> {
  return apiFetch<ArtifactVersionResponse>(endpoints.artifacts.versions(artifactId), {
    method: "POST",
    body,
  });
}

export function restoreVersion(
  artifactId: string,
  versionNumber: number,
): Promise<ArtifactRestoreResponse> {
  return apiFetch<ArtifactRestoreResponse>(endpoints.artifacts.restore(artifactId, versionNumber), {
    method: "POST",
  });
}

export function diffVersions(
  artifactId: string,
  fromVersion: number,
  toVersion: number,
): Promise<ArtifactDiffResponse> {
  const qs = buildQueryString({
    from_version: fromVersion,
    to_version: toVersion,
  });
  return apiFetch<ArtifactDiffResponse>(`${endpoints.artifacts.diff(artifactId)}${qs}`);
}
