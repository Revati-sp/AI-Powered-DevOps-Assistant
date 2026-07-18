import { describe, expect, it } from "vitest";
import { queryKeys } from "@/lib/api/query-keys";

describe("queryKeys", () => {
  it("builds stable auth and conversation keys", () => {
    expect(queryKeys.auth.currentUser()).toEqual(["auth", "currentUser"]);
    expect(queryKeys.conversations.list({ q: "pod" })).toEqual([
      "conversations",
      "list",
      { q: "pod" },
    ]);
    expect(queryKeys.conversations.detail("c1")).toEqual(["conversations", "detail", "c1"]);
  });

  it("includes organization filters in scoped keys", () => {
    const filters = { limit: 20, offset: 0 };
    expect(queryKeys.organizations.list(filters)).toEqual(["organizations", "list", filters]);
    expect(queryKeys.members.list("org-1", filters)).toEqual(["members", "org-1", "list", filters]);
    expect(queryKeys.policyPacks.list("org-1", { q: "cis" })).toEqual([
      "policyPacks",
      "org-1",
      "list",
      { q: "cis" },
    ]);
    expect(queryKeys.auditEvents.list("org-1", { action: "login" })).toEqual([
      "auditEvents",
      "org-1",
      "list",
      { action: "login" },
    ]);
  });

  it("builds artifact, version, and task keys", () => {
    expect(queryKeys.artifacts.list({ organization_id: "o1" })).toEqual([
      "artifacts",
      "list",
      { organization_id: "o1" },
    ]);
    expect(queryKeys.artifacts.detail("a1")).toEqual(["artifacts", "detail", "a1"]);
    expect(queryKeys.versions.list("a1", { limit: 10 })).toEqual([
      "versions",
      "a1",
      "list",
      { limit: 10 },
    ]);
    expect(queryKeys.tasks.list({})).toEqual(["tasks", "list", {}]);
    expect(queryKeys.tasks.detail("t1")).toEqual(["tasks", "detail", "t1"]);
  });
});
