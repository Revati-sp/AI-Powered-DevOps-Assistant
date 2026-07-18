import type { BrowserContext, Page } from "@playwright/test";

export const MOCK_USER = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "e2e@example.com",
  username: "e2e-user",
  role: "user",
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
} as const;

const EMPTY_PAGE = {
  items: [],
  total: 0,
  limit: 20,
  offset: 0,
};

function json(data: unknown, status = 200) {
  return {
    status,
    contentType: "application/json",
    body: JSON.stringify(data),
  };
}

/**
 * Mock Next.js auth route handlers so e2e never needs a real backend.
 */
export async function mockAuthRoutes(page: Page): Promise<void> {
  await page.route("**/api/auth/me", async (route) => {
    if (route.request().method() !== "GET") {
      await route.fallback();
      return;
    }
    await route.fulfill(json({ success: true, data: MOCK_USER }));
  });

  await page.route("**/api/auth/login", async (route) => {
    if (route.request().method() !== "POST") {
      await route.fallback();
      return;
    }
    await route.fulfill(json({ success: true, expires_in: 900 }));
  });

  await page.route("**/api/auth/register", async (route) => {
    if (route.request().method() !== "POST") {
      await route.fallback();
      return;
    }
    await route.fulfill(json({ success: true, data: MOCK_USER }));
  });

  await page.route("**/api/auth/logout", async (route) => {
    await route.fulfill(json({ success: true, data: null }));
  });

  await page.route("**/api/auth/logout-all", async (route) => {
    await route.fulfill(json({ success: true, data: null }));
  });
}

/**
 * Mock BFF proxy traffic (`/api/bff/**`) with empty, successful envelopes.
 */
export async function mockBffRoutes(page: Page): Promise<void> {
  await page.route("**/api/bff/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace(/^\/api\/bff/, "");

    if (path.startsWith("/api/v1/chat/conversations")) {
      await route.fulfill(json({ success: true, data: [] }));
      return;
    }

    if (
      path.startsWith("/api/v1/artifacts") ||
      path.startsWith("/api/v1/tasks") ||
      path.startsWith("/api/v1/organizations")
    ) {
      await route.fulfill(json({ success: true, data: EMPTY_PAGE }));
      return;
    }

    await route.fulfill(json({ success: true, data: null }));
  });
}

export async function mockAuthenticatedApis(page: Page): Promise<void> {
  await mockAuthRoutes(page);
  await mockBffRoutes(page);
}

/**
 * Session cookies for middleware. Values are opaque — BFF/auth are mocked.
 */
export async function setSessionCookies(
  context: BrowserContext,
  baseURL = "http://127.0.0.1:3000",
): Promise<void> {
  const url = new URL(baseURL);
  await context.addCookies([
    {
      name: "ada_access",
      value: "e2e-access-token",
      domain: url.hostname,
      path: "/",
      httpOnly: true,
      sameSite: "Lax",
      secure: false,
    },
    {
      name: "ada_refresh",
      value: "e2e-refresh-token",
      domain: url.hostname,
      path: "/",
      httpOnly: true,
      sameSite: "Lax",
      secure: false,
    },
  ]);
}
