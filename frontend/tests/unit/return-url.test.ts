import { describe, expect, it } from "vitest";
import { getSafeReturnUrl } from "@/lib/utils/return-url";

describe("getSafeReturnUrl", () => {
  it("allows relative same-origin paths", () => {
    expect(getSafeReturnUrl("/dashboard")).toBe("/dashboard");
    expect(getSafeReturnUrl("/orgs/123/artifacts?tab=diff")).toBe("/orgs/123/artifacts?tab=diff");
  });

  it("rejects absolute and protocol-relative URLs", () => {
    expect(getSafeReturnUrl("https://evil.example/phish")).toBe("/dashboard");
    expect(getSafeReturnUrl("//evil.example/phish")).toBe("/dashboard");
    expect(getSafeReturnUrl("/\\evil.example")).toBe("/dashboard");
  });

  it("uses the provided fallback for nullish or empty values", () => {
    expect(getSafeReturnUrl(null, "/home")).toBe("/home");
    expect(getSafeReturnUrl(undefined)).toBe("/dashboard");
    expect(getSafeReturnUrl("   ")).toBe("/dashboard");
  });
});
