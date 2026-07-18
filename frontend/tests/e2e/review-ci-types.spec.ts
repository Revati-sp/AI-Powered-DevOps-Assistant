import { expect, test } from "@playwright/test";

import { mockAuthenticatedApis, setSessionCookies } from "./helpers/auth";

const REVIEW_OK = {
  success: true,
  data: {
    score: 70,
    summary: "Deterministic review found issues.",
    findings: [
      {
        severity: "critical",
        title: "Remote script piped to shell",
        description: "Piping curl output to shell is dangerous.",
        recommendation: "Vendor scripts and verify checksums.",
        line: 4,
        source: "static",
      },
    ],
    built_in_findings: [
      {
        severity: "critical",
        title: "Remote script piped to shell",
        description: "Piping curl output to shell is dangerous.",
        recommendation: "Vendor scripts and verify checksums.",
        line: 4,
        source: "static",
      },
    ],
    organization_policy_findings: [],
    llm_findings: [],
    improved_content: null,
    disclaimer: "Human review required.",
  },
};

test.describe("configuration review CI types", () => {
  test.beforeEach(async ({ page, context, baseURL }) => {
    await setSessionCookies(context, baseURL ?? "http://127.0.0.1:3000");
    await mockAuthenticatedApis(page);

    await page.route("**/api/bff/api/v1/review", async (route) => {
      if (route.request().method() !== "POST") {
        await route.fallback();
        return;
      }
      const body = route.request().postDataJSON() as { type?: string };
      expect(["gitlab-ci", "jenkins"]).toContain(body.type);
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(REVIEW_OK),
      });
    });
  });

  test("reviews sample GitLab CI and shows findings", async ({ page }) => {
    await page.goto("/reviews");
    await expect(page.getByRole("heading", { name: /configuration review/i })).toBeVisible();

    await page.getByLabel(/configuration type/i).click();
    await page.getByRole("option", { name: "GitLab CI" }).click();
    await expect(page.getByText(/\.gitlab-ci\.yml/i)).toBeVisible();

    await page.getByRole("button", { name: /load sample/i }).click();
    await page.getByRole("button", { name: /^run review$/i }).click();

    await expect(page.getByText(/remote script piped to shell/i)).toBeVisible();
    await expect(page.getByText(/gitlab ci/i).first()).toBeVisible();
  });

  test("reviews sample Jenkins and shows findings", async ({ page }) => {
    await page.goto("/reviews");

    await page.getByLabel(/configuration type/i).click();
    await page.getByRole("option", { name: "Jenkins" }).click();
    await expect(page.getByText(/Jenkinsfile/i).first()).toBeVisible();

    await page.getByRole("button", { name: /load sample/i }).click();
    await page.getByRole("button", { name: /^run review$/i }).click();

    await expect(page.getByText(/remote script piped to shell/i)).toBeVisible();
  });
});
