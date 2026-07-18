import { expect, test } from "@playwright/test";

import { mockAuthenticatedApis, setSessionCookies } from "./helpers/auth";

const artifact = {
  id: "artifact-1",
  user_id: "11111111-1111-1111-1111-111111111111",
  organization_id: null,
  artifact_type: "dockerfile",
  name: "Production Dockerfile",
  description: "Container build",
  current_version_number: 1,
  created_at: "2026-07-17T12:00:00Z",
  updated_at: "2026-07-17T12:00:00Z",
  is_favorited: false,
  archived_at: null,
  tags: ["production"],
};

test("mocks artifact tag, favorite, archive, filter, and search workflows", async ({
  page,
  context,
  baseURL,
}) => {
  await setSessionCookies(context, baseURL ?? "http://127.0.0.1:3000");
  await mockAuthenticatedApis(page);
  await page.route("**/api/bff/**/artifacts**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    if (path.endsWith("/tags/list")) {
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: [
            {
              id: "tag-1",
              name: "production",
              organization_id: null,
              user_id: artifact.user_id,
              color: null,
              created_at: artifact.created_at,
            },
          ],
        }),
      });
      return;
    }
    if (
      path.endsWith("/favorite") ||
      path.endsWith("/archive") ||
      path.endsWith("/unarchive")
    ) {
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({ success: true, data: null }),
      });
      return;
    }
    if (path.endsWith("/tags")) {
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({ success: true, data: ["production"] }),
      });
      return;
    }
    const search = url.searchParams.get("search") ?? "";
    const tags = url.searchParams.getAll("tags");
    const includeArchived = url.searchParams.get("include_archived") === "true";
    const matches =
      (!search || artifact.name.toLowerCase().includes(search.toLowerCase())) &&
      (!tags.length || tags.includes("production")) &&
      (includeArchived || artifact.archived_at === null);
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: { items: matches ? [artifact] : [], total: matches ? 1 : 0, limit: 20, offset: 0 },
      }),
    });
  });

  await page.goto("/artifacts");
  await expect(page.getByText("Production Dockerfile")).toBeVisible();
  await page.getByRole("button", { name: "Add to favorites" }).click();

  await page.getByLabel("Search").fill("production");
  await expect(page).toHaveURL(/search=production/);

  await page.getByLabel("Filter by tag").click();
  await page.getByRole("option", { name: "production", exact: true }).click();
  await expect(page).toHaveURL(/tag=production/);
  await expect(page).toHaveURL(/search=production/);

  await page.getByLabel("Include archived").click();
  await expect(page).toHaveURL(/include_archived=true/);
});
