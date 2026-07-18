import { expect, test } from "@playwright/test";

import { mockAuthenticatedApis, setSessionCookies } from "./helpers/auth";

test("submits organization-scoped async log analysis and polls task", async ({
  page,
  context,
  baseURL,
}) => {
  await setSessionCookies(context, baseURL ?? "http://127.0.0.1:3000");
  await mockAuthenticatedApis(page);

  const organizationId = "22222222-2222-2222-2222-222222222222";
  await page.route("**/api/bff/**/organizations**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          items: [
            {
              id: organizationId,
              name: "Platform Team",
              slug: "platform-team",
              created_at: "2026-07-17T12:00:00Z",
              updated_at: "2026-07-17T12:00:00Z",
            },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        },
      }),
    });
  });

  await page.route(`**/api/bff/**/organizations/${organizationId}/members**`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          items: [
            {
              user_id: "11111111-1111-1111-1111-111111111111",
              role: "member",
              username: "e2e-user",
              email: "e2e@example.com",
              joined_at: "2026-07-17T12:00:00Z",
            },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        },
      }),
    });
  });

  let capturedBody: Record<string, unknown> | null = null;
  await page.route("**/api/bff/**/logs/analyze/async**", async (route) => {
    capturedBody = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          task_id: "task-log-1",
          status: "queued",
          analysis_id: "analysis-log-1",
          organization_id: organizationId,
        },
      }),
    });
  });

  await page.route("**/api/bff/**/tasks/task-log-1**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          id: "task-log-1",
          task_id: "task-log-1",
          status: "succeeded",
          progress: 100,
          organization_id: organizationId,
          result_json: {
            summary: "Crash loop detected",
            severity: "high",
            detected_errors: ["CrashLoopBackOff"],
            possible_causes: ["Bad image"],
            recommended_actions: ["Roll back"],
            diagnostic_commands: ["kubectl describe pod x"],
            confidence: 0.9,
            disclaimer: "Review only",
          },
          error_message: null,
        },
      }),
    });
  });

  await page.addInitScript((orgId) => {
    localStorage.setItem(
      "ada-workspace",
      JSON.stringify({ state: { currentOrganizationId: orgId }, version: 0 }),
    );
  }, organizationId);

  await page.goto("/logs");
  await page.getByLabel("Analysis workspace").click();
  await page.getByRole("option", { name: "Platform Team" }).click();
  await page.getByRole("checkbox", { name: /Run asynchronously/i }).check();

  const editor = page.getByRole("textbox", { name: "Editor content" });
  await editor.click({ force: true });
  await page.keyboard.type("CrashLoopBackOff\nERROR: Job failed\n", { delay: 5 });

  await page.getByRole("button", { name: "Analyze logs" }).click();
  await expect.poll(() => capturedBody?.organization_id).toBe(organizationId);
  await expect(page.getByText("Crash loop detected")).toBeVisible({ timeout: 10_000 });
});
