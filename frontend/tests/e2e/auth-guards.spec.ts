import { test, expect } from "@playwright/test";

test.describe("auth guards", () => {
  test("redirects unauthenticated users from protected routes to login", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page).toHaveURL(/\/login/);
    await expect(page).toHaveURL(/returnUrl=/);
    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
  });

  test("preserves returnUrl for nested protected paths", async ({ page }) => {
    await page.goto("/generators/dockerfile");

    await expect(page).toHaveURL(/\/login/);
    const url = new URL(page.url());
    expect(decodeURIComponent(url.searchParams.get("returnUrl") ?? "")).toBe(
      "/generators/dockerfile",
    );
  });
});
