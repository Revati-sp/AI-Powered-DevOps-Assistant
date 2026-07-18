import { describe, expect, it } from "vitest";

import { chatComposerSchema } from "@/features/chat/schemas";
import { CHAT_MESSAGE_MAX } from "@/lib/constants/app";

describe("chatComposerSchema", () => {
  it("accepts a valid message and provider", () => {
    const result = chatComposerSchema.safeParse({
      message: "How do I fix CrashLoopBackOff?",
      provider: "gemini",
    });
    expect(result.success).toBe(true);
  });

  it("trims whitespace and rejects empty messages", () => {
    expect(
      chatComposerSchema.safeParse({
        message: "   ",
        provider: "llama",
      }).success,
    ).toBe(false);

    expect(
      chatComposerSchema.safeParse({
        message: "",
        provider: "mistral",
      }).success,
    ).toBe(false);
  });

  it("rejects messages over the character limit", () => {
    const result = chatComposerSchema.safeParse({
      message: "a".repeat(CHAT_MESSAGE_MAX + 1),
      provider: "gemini",
    });
    expect(result.success).toBe(false);
  });

  it("rejects unknown providers", () => {
    const result = chatComposerSchema.safeParse({
      message: "hello",
      provider: "chatgpt",
    });
    expect(result.success).toBe(false);
  });
});
