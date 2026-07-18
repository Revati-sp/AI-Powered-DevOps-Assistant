import { describe, expect, it } from "vitest";
import { sanitizeFilename } from "@/lib/utils/filename";

describe("sanitizeFilename", () => {
  it("strips path segments", () => {
    expect(sanitizeFilename("../../etc/passwd")).toBe("passwd");
    expect(sanitizeFilename("C:\\Users\\me\\report.log")).toBe("report.log");
  });

  it("removes null bytes and dangerous characters", () => {
    expect(sanitizeFilename("bad\0name<>:|?*.txt")).toBe("badname______.txt");
  });

  it("falls back for empty or traversal-only names", () => {
    expect(sanitizeFilename("")).toBe("download.txt");
    expect(sanitizeFilename("...")).toBe("download.txt");
    expect(sanitizeFilename("///")).toBe("download.txt");
    expect(sanitizeFilename("..", "artifact.yaml")).toBe("artifact.yaml");
  });

  it("truncates overly long names while preserving extension when practical", () => {
    const long = `${"a".repeat(250)}.yaml`;
    const result = sanitizeFilename(long);
    expect(result.length).toBeLessThanOrEqual(200);
    expect(result.endsWith(".yaml")).toBe(true);
  });
});
