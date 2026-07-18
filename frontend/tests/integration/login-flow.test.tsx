import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";

import { LoginForm } from "@/components/auth/login-form";
import { AuthProvider } from "@/providers/auth-provider";

const push = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh, replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams("returnUrl=%2Fchat"),
}));

const server = setupServer(
  http.get("/api/auth/me", () =>
    HttpResponse.json(
      {
        success: false,
        error: { code: "UNAUTHORIZED", message: "Not authenticated" },
      },
      { status: 401 },
    ),
  ),
  http.post("/api/auth/login", async ({ request }) => {
    const body = (await request.json()) as {
      username?: string;
      password?: string;
    };
    if (body.username === "good" && body.password === "password123456") {
      return HttpResponse.json({ success: true, expires_in: 900 });
    }
    return HttpResponse.json(
      {
        success: false,
        error: { code: "UNAUTHORIZED", message: "Invalid credentials" },
      },
      { status: 401 },
    );
  }),
);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
  push.mockClear();
  refresh.mockClear();
});
afterAll(() => server.close());

function renderLoginForm() {
  return render(
    <AuthProvider>
      <LoginForm />
    </AuthProvider>,
  );
}

describe("login flow", () => {
  it("shows validation errors for empty fields", async () => {
    const user = userEvent.setup();
    renderLoginForm();

    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText(/username is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it("shows a generic failure message on invalid credentials", async () => {
    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByLabelText(/username/i), "bad");
    await user.type(screen.getByLabelText(/^password$/i), "wrong-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText(/invalid username or password/i)).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it("redirects to the safe returnUrl on success", async () => {
    server.use(
      http.get("/api/auth/me", () =>
        HttpResponse.json({
          success: true,
          data: {
            id: "11111111-1111-1111-1111-111111111111",
            email: "good@example.com",
            username: "good",
            role: "user",
            is_active: true,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        }),
      ),
    );

    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByLabelText(/username/i), "good");
    await user.type(screen.getByLabelText(/^password$/i), "password123456");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(push).toHaveBeenCalledWith("/chat");
    });
  });
});
