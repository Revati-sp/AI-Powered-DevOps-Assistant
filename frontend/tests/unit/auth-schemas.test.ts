import { describe, expect, it } from "vitest";

import {
  changePasswordSchema,
  forgotPasswordSchema,
  loginSchema,
  registerSchema,
  resetPasswordSchema,
} from "@/features/auth/schemas";
import { inviteMemberSchema } from "@/features/organizations/schemas";
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

describe("forgotPasswordSchema", () => {
  it("accepts a valid email", () => {
    expect(forgotPasswordSchema.safeParse({ email: "user@example.com" }).success).toBe(true);
  });

  it("rejects empty or invalid email", () => {
    expect(forgotPasswordSchema.safeParse({ email: "" }).success).toBe(false);
    expect(forgotPasswordSchema.safeParse({ email: "not-an-email" }).success).toBe(false);
  });
});

describe("resetPasswordSchema", () => {
  it("accepts matching passwords", () => {
    const password = "a".repeat(PASSWORD_MIN);
    expect(
      resetPasswordSchema.safeParse({
        new_password: password,
        confirm_password: password,
      }).success,
    ).toBe(true);
  });

  it("rejects mismatched confirmation", () => {
    expect(
      resetPasswordSchema.safeParse({
        new_password: "a".repeat(PASSWORD_MIN),
        confirm_password: "b".repeat(PASSWORD_MIN),
      }).success,
    ).toBe(false);
  });

  it("rejects short passwords", () => {
    expect(
      resetPasswordSchema.safeParse({
        new_password: "short",
        confirm_password: "short",
      }).success,
    ).toBe(false);
  });
});

describe("changePasswordSchema", () => {
  it("accepts valid password change values", () => {
    const password = "a".repeat(PASSWORD_MIN);
    expect(
      changePasswordSchema.safeParse({
        current_password: "old-password-123",
        new_password: password,
        confirm_password: password,
      }).success,
    ).toBe(true);
  });

  it("rejects when new password matches current password", () => {
    const password = "same-password-12";
    expect(
      changePasswordSchema.safeParse({
        current_password: password,
        new_password: password,
        confirm_password: password,
      }).success,
    ).toBe(false);
  });
});

describe("inviteMemberSchema", () => {
  it("accepts a valid invitation payload", () => {
    expect(
      inviteMemberSchema.safeParse({
        email: "invitee@example.com",
        role: "member",
      }).success,
    ).toBe(true);
  });
});
