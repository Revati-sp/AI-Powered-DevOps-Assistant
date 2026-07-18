import { test, expect } from "@playwright/test";

import { mockAuthenticatedApis, setSessionCookies } from "./helpers/auth";

test.describe("mobile navigation", () => {
  test.beforeEach(async ({ page, context, baseURL }) => {
    await setSessionCookies(context, baseURL ?? "http://127.0.0.1:3000");
    await mockAuthenticatedApis(page);
  });

  test("opens mobile nav sheet from header menu", async ({ page }) => {
    // This file is matched by the Playwright "mobile" project (Pixel 5).
    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: /^dashboard$/i })).toBeVisible();

    await page.getByRole("button", { name: /open navigation/i }).click();

    const sheet = page.getByRole("dialog");
    await expect(sheet).toBeVisible();
    await expect(sheet.getByRole("link", { name: /dashboard/i }).first()).toBeVisible();
  });
});
