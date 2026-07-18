import { test, expect } from "@playwright/test";

import { mockAuthenticatedApis, setSessionCookies } from "./helpers/auth";

test.describe("theme toggle", () => {
  test.beforeEach(async ({ page, context, baseURL }) => {
    await setSessionCookies(context, baseURL ?? "http://127.0.0.1:3000");
    await mockAuthenticatedApis(page);
  });

  test("switches to dark mode from header control", async ({ page }) => {
    await page.goto("/dashboard");

    await page.getByRole("button", { name: /toggle theme/i }).click();
    await page.getByRole("menuitemradio", { name: /dark/i }).click();

    await expect(page.locator("html")).toHaveClass(/dark/);
  });
});
