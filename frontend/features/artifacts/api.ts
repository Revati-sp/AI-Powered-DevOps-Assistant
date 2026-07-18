import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { buildQueryString } from "@/lib/api/query-string";

import type {
  ArtifactCreateRequest,
  ArtifactDetailResponse,
  ArtifactDiffResponse,
  ArtifactRestoreResponse,
  ArtifactsPage,
  ArtifactSummaryResponse,
  ArtifactTagAssignRequest,
  ArtifactTagCreateRequest,
  ArtifactTagResponse,
  ArtifactUpdateRequest,
  ArtifactVersionCreateRequest,
  ArtifactVersionResponse,
  VersionsPage,
} from "./types";

export type ListArtifactsParams = {
  organization_id?: string | null;
  limit?: number;
  offset?: number;
  search?: string;
  tags?: string[];
  favorites_only?: boolean;
  include_archived?: boolean;
  archived_only?: boolean;
  artifact_type?: string;
  created_from?: string;
  created_to?: string;
  updated_from?: string;
  updated_to?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
};

export function listArtifacts(params: ListArtifactsParams = {}): Promise<ArtifactsPage> {
  const qs = buildQueryString({
    organization_id: params.organization_id ?? undefined,
    limit: params.limit ?? 20,
    offset: params.offset ?? 0,
    search: params.search?.trim() || undefined,
    tags: params.tags?.length ? params.tags : undefined,
    favorites_only: params.favorites_only ? true : undefined,
    include_archived: params.include_archived ? true : undefined,
    archived_only: params.archived_only ? true : undefined,
    artifact_type: params.artifact_type,
    created_from: params.created_from,
    created_to: params.created_to,
    updated_from: params.updated_from,
    updated_to: params.updated_to,
    sort_by: params.sort_by,
    sort_order: params.sort_order,
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

export type ListTagsParams = {
  organization_id?: string | null;
};

export function listTags(params: ListTagsParams = {}): Promise<ArtifactTagResponse[]> {
  const qs = buildQueryString({
    organization_id: params.organization_id ?? undefined,
  });
  return apiFetch<ArtifactTagResponse[]>(`${endpoints.artifacts.tagsList()}${qs}`);
}

export function createTag(
  body: ArtifactTagCreateRequest,
  params: ListTagsParams = {},
): Promise<ArtifactTagResponse> {
  const qs = buildQueryString({
    organization_id: params.organization_id ?? undefined,
  });
  return apiFetch<ArtifactTagResponse>(`${endpoints.artifacts.tags()}${qs}`, {
    method: "POST",
    body,
  });
}

export function addArtifactTag(
  artifactId: string,
  body: ArtifactTagAssignRequest,
): Promise<ArtifactTagResponse[]> {
  return apiFetch<ArtifactTagResponse[]>(endpoints.artifacts.artifactTags(artifactId), {
    method: "POST",
    body,
  });
}

export function removeArtifactTag(
  artifactId: string,
  tagId: string,
): Promise<ArtifactTagResponse[]> {
  return apiFetch<ArtifactTagResponse[]>(endpoints.artifacts.artifactTag(artifactId, tagId), {
    method: "DELETE",
  });
}

export function favoriteArtifact(artifactId: string): Promise<void> {
  return apiFetch<void>(endpoints.artifacts.favorite(artifactId), { method: "POST" });
}

export function unfavoriteArtifact(artifactId: string): Promise<void> {
  return apiFetch<void>(endpoints.artifacts.favorite(artifactId), { method: "DELETE" });
}

export function archiveArtifact(artifactId: string): Promise<ArtifactSummaryResponse> {
  return apiFetch<ArtifactSummaryResponse>(endpoints.artifacts.archive(artifactId), {
    method: "POST",
  });
}

export function unarchiveArtifact(artifactId: string): Promise<ArtifactSummaryResponse> {
  return apiFetch<ArtifactSummaryResponse>(endpoints.artifacts.unarchive(artifactId), {
    method: "POST",
  });
}
