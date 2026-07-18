export type QueryFilters = Record<string, unknown>;

/**
 * TanStack Query key factory. Include filter objects in keys for cache isolation.
 */
export const queryKeys = {
  auth: {
    all: () => ["auth"] as const,
    currentUser: () => ["auth", "currentUser"] as const,
  },
  conversations: {
    all: () => ["conversations"] as const,
    list: (filters: QueryFilters = {}) => ["conversations", "list", filters] as const,
    detail: (id: string) => ["conversations", "detail", id] as const,
  },
  organizations: {
    all: () => ["organizations"] as const,
    list: (filters: QueryFilters = {}) => ["organizations", "list", filters] as const,
    detail: (id: string) => ["organizations", "detail", id] as const,
  },
  members: {
    all: (organizationId: string) => ["members", organizationId] as const,
    list: (organizationId: string, filters: QueryFilters = {}) =>
      ["members", organizationId, "list", filters] as const,
  },
  artifacts: {
    all: () => ["artifacts"] as const,
    list: (filters: QueryFilters = {}) => ["artifacts", "list", filters] as const,
    detail: (id: string) => ["artifacts", "detail", id] as const,
  },
  versions: {
    all: (artifactId: string) => ["versions", artifactId] as const,
    list: (artifactId: string, filters: QueryFilters = {}) =>
      ["versions", artifactId, "list", filters] as const,
    detail: (artifactId: string, versionNumber: number | string) =>
      ["versions", artifactId, "detail", versionNumber] as const,
  },
  policyPacks: {
    all: (organizationId: string) => ["policyPacks", organizationId] as const,
    list: (organizationId: string, filters: QueryFilters = {}) =>
      ["policyPacks", organizationId, "list", filters] as const,
    detail: (organizationId: string, packId: string) =>
      ["policyPacks", organizationId, "detail", packId] as const,
  },
  tasks: {
    all: () => ["tasks"] as const,
    list: (filters: QueryFilters = {}) => ["tasks", "list", filters] as const,
    detail: (id: string) => ["tasks", "detail", id] as const,
  },
  auditEvents: {
    all: (organizationId: string) => ["auditEvents", organizationId] as const,
    list: (organizationId: string, filters: QueryFilters = {}) =>
      ["auditEvents", organizationId, "list", filters] as const,
  },
} as const;
