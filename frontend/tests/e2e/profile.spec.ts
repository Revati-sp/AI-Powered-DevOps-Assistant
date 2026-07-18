import { expect, test } from "@playwright/test";

import { mockAuthenticatedApis, setSessionCookies } from "./helpers/auth";

test("updates profile values after sign in", async ({ page, context, baseURL }) => {
  await mockAuthenticatedApis(page);
  await page.goto("/login");
  await page.getByLabel(/username/i).fill("e2e-user");
  await page.getByLabel(/^password$/i).fill("password");
  await page.getByRole("button", { name: /^sign in$/i }).click();

  await setSessionCookies(context, baseURL ?? "http://127.0.0.1:3000");
  await page.goto("/settings/profile");

  await page.getByLabel(/display name/i).fill("Updated E2E User");
  await page.getByLabel(/job title/i).fill("Platform Engineer");
  await page.getByRole("button", { name: /save changes/i }).click();

  await expect(page.getByLabel(/display name/i)).toHaveValue("Updated E2E User");
  await expect(page.getByLabel(/job title/i)).toHaveValue("Platform Engineer");
});
