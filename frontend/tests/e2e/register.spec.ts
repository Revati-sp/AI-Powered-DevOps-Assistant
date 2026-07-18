import { test, expect } from "@playwright/test";

import { mockAuthRoutes } from "./helpers/auth";

test.describe("register page", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthRoutes(page);
  });

  test("renders create-account form", async ({ page }) => {
    await page.goto("/register");

    await expect(page.getByRole("heading", { name: /create account/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/username/i)).toBeVisible();
    await expect(page.getByLabel(/^password$/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /create account/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /sign in/i })).toBeVisible();
  });
});
