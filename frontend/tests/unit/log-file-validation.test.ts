import { describe, expect, it } from "vitest";

import { looksLikeBinaryText, validateLogFile } from "@/features/logs/file-validation";
import { MAX_UPLOAD_MB } from "@/lib/constants/app";

function makeFile(name: string, content: string, options?: { type?: string }): File {
  return new File([content], name, {
    type: options?.type ?? "text/plain",
  });
}

describe("validateLogFile", () => {
  it("accepts .log and .txt files", () => {
    expect(validateLogFile(makeFile("app.log", "error")).ok).toBe(true);
    expect(validateLogFile(makeFile("trace.txt", "line")).ok).toBe(true);
  });

  it("rejects empty or missing files", () => {
    expect(validateLogFile(null).ok).toBe(false);
    expect(validateLogFile(makeFile("empty.log", "")).ok).toBe(false);
  });

  it("rejects unsupported extensions", () => {
    const result = validateLogFile(makeFile("dump.bin", "abc"));
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe("extension");
    }
  });

  it("rejects oversized files", () => {
    const oversized = new File([new Uint8Array(MAX_UPLOAD_MB * 1024 * 1024 + 1)], "huge.log", {
      type: "text/plain",
    });
    const result = validateLogFile(oversized);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe("size");
    }
  });
});

describe("looksLikeBinaryText", () => {
  it("flags null bytes and high binary ratios", () => {
    expect(looksLikeBinaryText("hello\0world")).toBe(true);
    expect(looksLikeBinaryText("plain log line\n")).toBe(false);
  });
});
