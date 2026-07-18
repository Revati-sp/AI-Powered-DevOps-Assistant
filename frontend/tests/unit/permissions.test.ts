import { describe, expect, it } from "vitest";
import {
  ALL_PERMISSIONS,
  can,
  hasAllPermissions,
  hasAnyPermission,
  ROLE_PERMISSIONS,
  type OrgRole,
  type Permission,
} from "@/lib/permissions/rbac";

describe("ROLE_PERMISSIONS", () => {
  it("gives owner every permission", () => {
    expect(ROLE_PERMISSIONS.owner.size).toBe(ALL_PERMISSIONS.length);
    for (const permission of ALL_PERMISSIONS) {
      expect(can("owner", permission)).toBe(true);
    }
  });

  it("matches backend admin permissions", () => {
    const expected: Permission[] = [
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
    ];
    expect([...ROLE_PERMISSIONS.admin].sort()).toEqual(expected.sort());
    expect(can("admin", "organization.delete")).toBe(false);
  });

  it("matches backend member permissions", () => {
    expect(can("member", "artifact.write")).toBe(true);
    expect(can("member", "task.cancel")).toBe(true);
    expect(can("member", "member.manage")).toBe(false);
    expect(can("member", "audit.read")).toBe(false);
  });

  it("matches backend viewer permissions", () => {
    const role: OrgRole = "viewer";
    expect(can(role, "organization.read")).toBe(true);
    expect(can(role, "artifact.read")).toBe(true);
    expect(can(role, "policy.read")).toBe(true);
    expect(can(role, "resource.create")).toBe(false);
    expect(can(role, "artifact.write")).toBe(false);
  });
});

describe("permission helpers", () => {
  it("hasAnyPermission / hasAllPermissions", () => {
    expect(hasAnyPermission("viewer", ["member.manage", "organization.read"])).toBe(true);
    expect(hasAnyPermission("viewer", ["member.manage", "audit.read"])).toBe(false);
    expect(hasAllPermissions("admin", ["organization.read", "policy.manage"])).toBe(true);
    expect(hasAllPermissions("admin", ["organization.read", "organization.delete"])).toBe(false);
  });
});
