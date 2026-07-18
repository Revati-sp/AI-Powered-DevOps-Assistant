import { describe, expect, it } from "vitest";

import { loginSchema, registerSchema } from "@/features/auth/schemas";
import { PASSWORD_MIN } from "@/lib/constants/app";

describe("loginSchema", () => {
  it("accepts valid credentials", () => {
    const result = loginSchema.safeParse({
      username: "devops_user",
      password: "secret",
    });
    expect(result.success).toBe(true);
  });

  it("rejects empty username or password", () => {
    expect(loginSchema.safeParse({ username: "", password: "x" }).success).toBe(false);
    expect(loginSchema.safeParse({ username: "user", password: "" }).success).toBe(false);
  });
});

describe("registerSchema", () => {
  it("accepts a valid registration payload", () => {
    const result = registerSchema.safeParse({
      email: "user@example.com",
      username: "valid_user-1",
      password: "a".repeat(PASSWORD_MIN),
    });
    expect(result.success).toBe(true);
  });

  it("rejects short passwords", () => {
    const result = registerSchema.safeParse({
      email: "user@example.com",
      username: "valid_user",
      password: "short",
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid usernames and emails", () => {
    expect(
      registerSchema.safeParse({
        email: "not-an-email",
        username: "ok_user",
        password: "a".repeat(PASSWORD_MIN),
      }).success,
    ).toBe(false);

    expect(
      registerSchema.safeParse({
        email: "user@example.com",
        username: "bad user!",
        password: "a".repeat(PASSWORD_MIN),
      }).success,
    ).toBe(false);
  });
});
