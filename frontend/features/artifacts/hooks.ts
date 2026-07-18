"use client";

import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from "@tanstack/react-query";

import { queryKeys } from "@/lib/api/query-keys";

import {
  createArtifact,
  createVersion,
  deleteArtifact,
  diffVersions,
  getArtifact,
  getVersion,
  listArtifacts,
  listVersions,
  restoreVersion,
  updateArtifact,
  type ListArtifactsParams,
} from "./api";
import type {
  ArtifactCreateRequest,
  ArtifactDetailResponse,
  ArtifactDiffResponse,
  ArtifactsPage,
  ArtifactUpdateRequest,
  ArtifactVersionCreateRequest,
  ArtifactVersionResponse,
  VersionsPage,
} from "./types";

export function useArtifacts(
  params: ListArtifactsParams = {},
  options?: Omit<UseQueryOptions<ArtifactsPage>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.artifacts.list(params),
    queryFn: () => listArtifacts(params),
    ...options,
  });
}

export function useArtifact(
  artifactId: string,
  options?: Omit<UseQueryOptions<ArtifactDetailResponse>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.artifacts.detail(artifactId),
    queryFn: () => getArtifact(artifactId),
    enabled: Boolean(artifactId),
    ...options,
  });
}

export function useArtifactVersions(
  artifactId: string,
  params: { limit?: number; offset?: number } = {},
  options?: Omit<UseQueryOptions<VersionsPage>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.versions.list(artifactId, params),
    queryFn: () => listVersions(artifactId, params),
    enabled: Boolean(artifactId),
    ...options,
  });
}

export function useArtifactVersion(
  artifactId: string,
  versionNumber: number | null,
  options?: Omit<UseQueryOptions<ArtifactVersionResponse>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: queryKeys.versions.detail(artifactId, versionNumber ?? "none"),
    queryFn: () => getVersion(artifactId, versionNumber as number),
    enabled: Boolean(artifactId && versionNumber != null),
    ...options,
  });
}

export function useArtifactDiff(
  artifactId: string,
  fromVersion: number | null,
  toVersion: number | null,
  options?: Omit<UseQueryOptions<ArtifactDiffResponse>, "queryKey" | "queryFn">,
) {
  return useQuery({
    queryKey: ["versions", artifactId, "diff", fromVersion, toVersion] as const,
    queryFn: () => diffVersions(artifactId, fromVersion as number, toVersion as number),
    enabled: Boolean(artifactId && fromVersion != null && toVersion != null),
    ...options,
  });
}

export function useCreateArtifact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ArtifactCreateRequest) => createArtifact(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.artifacts.all(),
      });
    },
  });
}

export function useUpdateArtifact(artifactId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ArtifactUpdateRequest) => updateArtifact(artifactId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.artifacts.all(),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.artifacts.detail(artifactId),
      });
    },
  });
}

export function useDeleteArtifact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (artifactId: string) => deleteArtifact(artifactId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.artifacts.all(),
      });
    },
  });
}

export function useCreateVersion(artifactId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ArtifactVersionCreateRequest) => createVersion(artifactId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.artifacts.detail(artifactId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.versions.all(artifactId),
      });
    },
  });
}

export function useRestoreVersion(artifactId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (versionNumber: number) => restoreVersion(artifactId, versionNumber),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.artifacts.detail(artifactId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.versions.all(artifactId),
      });
    },
  });
}
