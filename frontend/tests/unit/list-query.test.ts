import { describe, expect, it } from "vitest";

import { parseListQuery, serializeListQuery } from "@/lib/url/list-query";

describe("list query helpers", () => {
  it("parses list filter state from URL parameters", () => {
    expect(
      parseListQuery(
        new URLSearchParams(
          "page=3&search=nginx&artifact_type=dockerfile&favorites_only=true&sort_by=name&sort_order=asc",
        ),
      ),
    ).toMatchObject({
      page: 3,
      search: "nginx",
      artifactType: "dockerfile",
      favoritesOnly: true,
      sortBy: "name",
      sortOrder: "asc",
    });
  });

  it("omits default values when serializing", () => {
    expect(serializeListQuery({ page: 1, favoritesOnly: false })).toBe("");
    expect(serializeListQuery({ page: 2, search: "nginx", sortOrder: "desc" })).toBe(
      "page=2&search=nginx&sort_order=desc",
    );
  });

  it("preserves unrelated URL params on partial updates", () => {
    expect(
      serializeListQuery({ tag: "production", page: 1 }, new URLSearchParams("search=nginx")),
    ).toBe("search=nginx&tag=production");
  });
});
