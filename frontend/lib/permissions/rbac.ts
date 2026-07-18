/**
 * Mirrors backend `ROLE_PERMISSIONS` in `app/services/rbac.py` exactly.
 */

export type OrgRole = "owner" | "admin" | "member" | "viewer";

export type Permission =
  | "organization.read"
  | "organization.update"
  | "organization.delete"
  | "member.manage"
  | "artifact.read"
  | "artifact.write"
  | "policy.read"
  | "policy.manage"
  | "audit.read"
  | "task.cancel"
  | "resource.create";

export const ALL_PERMISSIONS: readonly Permission[] = [
  "organization.read",
  "organization.update",
  "organization.delete",
  "member.manage",
  "artifact.read",
  "artifact.write",
  "policy.read",
  "policy.manage",
  "audit.read",
  "task.cancel",
  "resource.create",
] as const;

export const ROLE_PERMISSIONS: Record<OrgRole, ReadonlySet<Permission>> = {
  owner: new Set(ALL_PERMISSIONS),
  admin: new Set<Permission>([
    "organization.read",
    "organization.update",
    "member.manage",
    "artifact.read",
    "artifact.write",
    "policy.read",
    "policy.manage",
    "audit.read",
    "task.cancel",
    "resource.create",
  ]),
  member: new Set<Permission>([
    "organization.read",
    "artifact.read",
    "artifact.write",
    "policy.read",
    "resource.create",
    "task.cancel",
  ]),
  viewer: new Set<Permission>(["organization.read", "artifact.read", "policy.read"]),
};

export function can(role: OrgRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.has(permission) ?? false;
}

export function hasAnyPermission(role: OrgRole, permissions: readonly Permission[]): boolean {
  return permissions.some((permission) => can(role, permission));
}

export function hasAllPermissions(role: OrgRole, permissions: readonly Permission[]): boolean {
  return permissions.every((permission) => can(role, permission));
}
