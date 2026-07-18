"use client";

import * as React from "react";

import { can, type OrgRole, type Permission } from "@/lib/permissions/rbac";

export type PermissionGateProps = {
  permission: Permission;
  role: OrgRole | null | undefined;
  fallback?: React.ReactNode;
  children: React.ReactNode;
};

/**
 * Client-side UX gate for org-scoped actions.
 * Backend authorization remains authoritative — never rely on this alone for security.
 */
export function PermissionGate({
  permission,
  role,
  fallback = null,
  children,
}: PermissionGateProps) {
  if (!role || !can(role, permission)) {
    return <>{fallback}</>;
  }
  return <>{children}</>;
}
