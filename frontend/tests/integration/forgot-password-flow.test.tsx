import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";

import { ForgotPasswordForm } from "@/components/auth/forgot-password-form";

const server = setupServer(
  http.post("/api/auth/forgot-password", async ({ request }) => {
    const body = (await request.json()) as { email?: string };
    if (body.email === "user@example.com") {
      return HttpResponse.json({
        success: true,
        data: { message: "If an account exists, instructions were sent." },
      });
    }
    return HttpResponse.json(
      {
        success: false,
        error: { code: "VALIDATION_ERROR", message: "Invalid email" },
      },
      { status: 400 },
    );
  }),
);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());

describe("forgot password flow", () => {
  it("shows validation errors for empty email", async () => {
    const user = userEvent.setup();
    render(<ForgotPasswordForm />);

    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
  });

  it("shows validation errors for invalid email", async () => {
    const user = userEvent.setup();
    render(<ForgotPasswordForm />);

    await user.type(screen.getByLabelText(/email/i), "not-an-email");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    expect(await screen.findByText(/enter a valid email/i)).toBeInTheDocument();
  });

  it("shows a non-enumerating success message", async () => {
    const user = userEvent.setup();
    render(<ForgotPasswordForm />);

    await user.type(screen.getByLabelText(/email/i), "user@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/if an account exists for that email address/i),
      ).toBeInTheDocument();
    });
  });
});
