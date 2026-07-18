import { expect, test } from "@playwright/test";

import { mockAuthenticatedApis, setSessionCookies } from "./helpers/auth";

const conversations = [
  {
    id: "conversation-1",
    title: "Gemini deployment",
    provider: "gemini",
    created_at: "2026-07-17T12:00:00Z",
    updated_at: "2026-07-17T12:00:00Z",
    organization_id: null,
  },
  {
    id: "conversation-2",
    title: "Mistral incident",
    provider: "mistral",
    created_at: "2026-07-16T12:00:00Z",
    updated_at: "2026-07-16T12:00:00Z",
    organization_id: null,
  },
];

test("searches, filters, and paginates conversations", async ({ page, context, baseURL }) => {
  await setSessionCookies(context, baseURL ?? "http://127.0.0.1:3000");
  await mockAuthenticatedApis(page);
  await page.route("**/api/bff/**/chat/conversations**", async (route) => {
    const url = new URL(route.request().url());
    const search = url.searchParams.get("search")?.toLowerCase() ?? "";
    const provider = url.searchParams.get("provider");
    const offset = Number(url.searchParams.get("offset") ?? "0");
    const limit = Number(url.searchParams.get("limit") ?? "30");
    const items = conversations.filter(
      (item) =>
        item.title.toLowerCase().includes(search) && (!provider || item.provider === provider),
    );
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          items: items.slice(offset, offset + limit),
          total: items.length,
          limit,
          offset,
        },
      }),
    });
  });

  await page.goto("/chat");
  await expect(page.getByText("Gemini deployment")).toBeVisible();

  await page.getByLabel("Search conversations").fill("incident");
  await expect(page.getByText("Mistral incident")).toBeVisible();
  await expect(page.getByText("Gemini deployment")).toHaveCount(0);

  await page.getByLabel("Search conversations").fill("");
  await page.getByLabel("Filter by provider").click();
  await page.getByRole("option", { name: "Gemini" }).click();
  await expect(page.getByText("Gemini deployment")).toBeVisible();
  await expect(page.getByText("Mistral incident")).toHaveCount(0);

  await page.getByLabel("Filter by provider").click();
  await page.getByRole("option", { name: "All providers" }).click();
  await expect(page.getByText("Gemini deployment")).toBeVisible();
  await expect(page.getByText("Mistral incident")).toBeVisible();
  await expect(page.getByText("1–2 of 2")).toBeVisible();
});
