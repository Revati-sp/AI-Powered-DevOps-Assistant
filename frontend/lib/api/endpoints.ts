const API_V1 = "/api/v1";

/**
 * Central path builders for FastAPI routes.
 * Paths are absolute from the API origin (or BFF mount).
 */
export const endpoints = {
  auth: {
    register: () => `${API_V1}/auth/register`,
    login: () => `${API_V1}/auth/login`,
    refresh: () => `${API_V1}/auth/refresh`,
    logout: () => `${API_V1}/auth/logout`,
    logoutAll: () => `${API_V1}/auth/logout-all`,
  },
  users: {
    me: () => `${API_V1}/users/me`,
  },
  chat: {
    chat: () => `${API_V1}/chat`,
    stream: () => `${API_V1}/chat/stream`,
    conversations: () => `${API_V1}/chat/conversations`,
    conversation: (conversationId: string) => `${API_V1}/chat/conversations/${conversationId}`,
    deleteConversation: (conversationId: string) =>
      `${API_V1}/chat/conversations/${conversationId}`,
  },
  logs: {
    analyze: () => `${API_V1}/logs/analyze`,
    analyzeUpload: () => `${API_V1}/logs/analyze/upload`,
    analyzeAsync: () => `${API_V1}/logs/analyze/async`,
  },
  generate: {
    dockerfile: () => `${API_V1}/generate/dockerfile`,
    kubernetes: () => `${API_V1}/generate/kubernetes`,
    pipeline: () => `${API_V1}/generate/pipeline`,
    command: () => `${API_V1}/generate/command`,
  },
  review: () => `${API_V1}/review`,
  artifacts: {
    list: () => `${API_V1}/artifacts`,
    detail: (artifactId: string) => `${API_V1}/artifacts/${artifactId}`,
    versions: (artifactId: string) => `${API_V1}/artifacts/${artifactId}/versions`,
    version: (artifactId: string, versionNumber: number | string) =>
      `${API_V1}/artifacts/${artifactId}/versions/${versionNumber}`,
    restore: (artifactId: string, versionNumber: number | string) =>
      `${API_V1}/artifacts/${artifactId}/versions/${versionNumber}/restore`,
    diff: (artifactId: string) => `${API_V1}/artifacts/${artifactId}/diff`,
  },
  organizations: {
    list: () => `${API_V1}/organizations`,
    detail: (organizationId: string) => `${API_V1}/organizations/${organizationId}`,
    members: (organizationId: string) => `${API_V1}/organizations/${organizationId}/members`,
    member: (organizationId: string, userId: string) =>
      `${API_V1}/organizations/${organizationId}/members/${userId}`,
  },
  policies: {
    packs: (organizationId: string) => `${API_V1}/organizations/${organizationId}/policy-packs`,
    pack: (organizationId: string, policyPackId: string) =>
      `${API_V1}/organizations/${organizationId}/policy-packs/${policyPackId}`,
    rules: (organizationId: string, policyPackId: string) =>
      `${API_V1}/organizations/${organizationId}/policy-packs/${policyPackId}/rules`,
    rule: (organizationId: string, policyPackId: string, ruleId: string) =>
      `${API_V1}/organizations/${organizationId}/policy-packs/${policyPackId}/rules/${ruleId}`,
  },
  audit: {
    events: (organizationId: string) => `${API_V1}/organizations/${organizationId}/audit-events`,
  },
  tasks: {
    list: () => `${API_V1}/tasks`,
    detail: (taskId: string) => `${API_V1}/tasks/${taskId}`,
    cancel: (taskId: string) => `${API_V1}/tasks/${taskId}/cancel`,
  },
  /** Health probes are mounted at the app root (not under /api/v1). */
  health: () => "/health",
  ready: () => "/ready",
} as const;
