import { describe, expect, it } from "vitest";

import { slugify } from "@/features/organizations/slugify";

describe("slugify", () => {
  it("lowercases and hyphenates words", () => {
    expect(slugify("Acme Corp")).toBe("acme-corp");
    expect(slugify("  My Team  ")).toBe("my-team");
  });

  it("strips punctuation and collapses separators", () => {
    expect(slugify("Hello, World!")).toBe("hello-world");
    expect(slugify("foo___bar")).toBe("foo-bar");
    expect(slugify('a\'s "org"')).toBe("as-org");
  });

  it("trims leading and trailing hyphens", () => {
    expect(slugify("---Edge---")).toBe("edge");
  });

  it("caps length at 64 characters", () => {
    const long = "a".repeat(80);
    expect(slugify(long).length).toBe(64);
  });
});
