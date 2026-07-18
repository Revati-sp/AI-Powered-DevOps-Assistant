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
    forgotPassword: () => `${API_V1}/auth/forgot-password`,
    resetPassword: () => `${API_V1}/auth/reset-password`,
    changePassword: () => `${API_V1}/auth/change-password`,
    sendVerification: () => `${API_V1}/auth/send-verification`,
    verifyEmail: () => `${API_V1}/auth/verify-email`,
    sessions: () => `${API_V1}/auth/sessions`,
    session: (sessionId: string) => `${API_V1}/auth/sessions/${sessionId}`,
  },
  invitations: {
    accept: () => `${API_V1}/invitations/accept`,
    decline: () => `${API_V1}/invitations/decline`,
  },
  users: {
    me: () => `${API_V1}/users/me`,
    meOnboarding: () => `${API_V1}/users/me/onboarding`,
    emailChangeRequest: () => `${API_V1}/users/me/email-change/request`,
    emailChangeConfirm: () => `${API_V1}/users/me/email-change/confirm`,
  },
  dashboard: {
    summary: () => `${API_V1}/dashboard/summary`,
    activity: () => `${API_V1}/dashboard/activity`,
    findings: () => `${API_V1}/dashboard/findings`,
    tasks: () => `${API_V1}/dashboard/tasks`,
  },
  usage: {
    me: () => `${API_V1}/usage/me`,
  },
  admin: {
    providers: {
      configs: () => `${API_V1}/admin/providers/configs`,
      config: (providerName: string) => `${API_V1}/admin/providers/configs/${providerName}`,
      routing: () => `${API_V1}/admin/providers/routing`,
      routingOperation: (operation: string) => `${API_V1}/admin/providers/routing/${operation}`,
      health: () => `${API_V1}/admin/providers/health`,
    },
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
    tagsList: () => `${API_V1}/artifacts/tags/list`,
    tags: () => `${API_V1}/artifacts/tags`,
    artifactTags: (artifactId: string) => `${API_V1}/artifacts/${artifactId}/tags`,
    artifactTag: (artifactId: string, tagId: string) =>
      `${API_V1}/artifacts/${artifactId}/tags/${tagId}`,
    favorite: (artifactId: string) => `${API_V1}/artifacts/${artifactId}/favorite`,
    archive: (artifactId: string) => `${API_V1}/artifacts/${artifactId}/archive`,
    unarchive: (artifactId: string) => `${API_V1}/artifacts/${artifactId}/unarchive`,
  },
  organizations: {
    list: () => `${API_V1}/organizations`,
    detail: (organizationId: string) => `${API_V1}/organizations/${organizationId}`,
    members: (organizationId: string) => `${API_V1}/organizations/${organizationId}/members`,
    member: (organizationId: string, userId: string) =>
      `${API_V1}/organizations/${organizationId}/members/${userId}`,
    invitations: (organizationId: string) =>
      `${API_V1}/organizations/${organizationId}/invitations`,
    invitation: (organizationId: string, invitationId: string) =>
      `${API_V1}/organizations/${organizationId}/invitations/${invitationId}`,
    resendInvitation: (organizationId: string, invitationId: string) =>
      `${API_V1}/organizations/${organizationId}/invitations/${invitationId}/resend`,
    usage: (organizationId: string) => `${API_V1}/organizations/${organizationId}/usage`,
    quotas: (organizationId: string) => `${API_V1}/organizations/${organizationId}/quotas`,
    providers: {
      configs: (organizationId: string) =>
        `${API_V1}/organizations/${organizationId}/providers/configs`,
      config: (organizationId: string, providerName: string) =>
        `${API_V1}/organizations/${organizationId}/providers/configs/${providerName}`,
      routing: (organizationId: string) =>
        `${API_V1}/organizations/${organizationId}/providers/routing`,
      routingOperation: (organizationId: string, operation: string) =>
        `${API_V1}/organizations/${organizationId}/providers/routing/${operation}`,
    },
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
