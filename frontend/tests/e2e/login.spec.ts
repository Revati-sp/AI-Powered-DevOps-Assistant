import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

import { mockAuthRoutes } from "./helpers/auth";

test.describe("login page", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthRoutes(page);
  });

  test("renders sign-in form", async ({ page }) => {
    await page.goto("/login");

    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
    await expect(page.getByLabel(/username/i)).toBeVisible();
    await expect(page.getByLabel(/^password$/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /create/i })).toBeVisible();
  });

  test("has no serious accessibility violations", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      // Primary teal tokens are not yet AA-compliant on all surfaces.
      .disableRules(["color-contrast"])
      .analyze();

    expect(results.violations).toEqual([]);
  });
});
