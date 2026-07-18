"use client";

import { useMutation } from "@tanstack/react-query";

import {
  generateCommand,
  generateDockerfile,
  generateKubernetes,
  generatePipeline,
} from "@/features/generators/api";
import type {
  DockerfileRequest,
  KubernetesRequest,
  PipelineRequest,
  ShellCommandRequest,
} from "@/features/generators/types";

export function useGenerateDockerfile() {
  return useMutation({
    mutationFn: (body: DockerfileRequest) => generateDockerfile(body),
  });
}

export function useGenerateKubernetes() {
  return useMutation({
    mutationFn: (body: KubernetesRequest) => generateKubernetes(body),
  });
}

export function useGeneratePipeline() {
  return useMutation({
    mutationFn: (body: PipelineRequest) => generatePipeline(body),
  });
}

export function useGenerateCommand() {
  return useMutation({
    mutationFn: (body: ShellCommandRequest) => generateCommand(body),
  });
}
