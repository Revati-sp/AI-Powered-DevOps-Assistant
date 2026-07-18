import { test, expect } from "@playwright/test";

import { mockAuthenticatedApis, setSessionCookies } from "./helpers/auth";

test.describe("dashboard (authenticated)", () => {
  test.beforeEach(async ({ page, context, baseURL }) => {
    await setSessionCookies(context, baseURL ?? "http://127.0.0.1:3000");
    await mockAuthenticatedApis(page);
  });

  test("loads dashboard when session cookies are present", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole("heading", { name: /^dashboard$/i })).toBeVisible();
    await expect(page.getByRole("main")).toContainText(/recent activity/i);
  });
});
