import { describe, expect, it } from "vitest";
import {
  ApiClientError,
  isApiClientError,
  parseErrorResponse,
  shouldRetryStatus,
} from "@/lib/api/errors";

describe("parseErrorResponse", () => {
  it("parses the backend ErrorResponse envelope", () => {
    const headers = new Headers({
      "X-Request-ID": "hdr-req-1",
      "Retry-After": "30",
    });

    const error = parseErrorResponse(
      429,
      {
        success: false,
        error: {
          code: "RATE_LIMITED",
          message: "Too many requests",
          details: {
            retry_after_seconds: 12,
            request_id: "detail-req-1",
            category: "api",
          },
        },
      },
      headers,
    );

    expect(error).toMatchObject({
      status: 429,
      code: "RATE_LIMITED",
      message: "Too many requests",
      requestId: "detail-req-1",
      retryAfterSeconds: 12,
    });
  });

  it("falls back to Retry-After and X-Request-ID headers", () => {
    const headers = new Headers({
      "Retry-After": "45",
      "X-Request-ID": "hdr-only",
    });

    const error = parseErrorResponse(
      503,
      {
        success: false,
        error: {
          code: "SERVICE_UNAVAILABLE",
          message: "Unavailable",
          details: {},
        },
      },
      headers,
    );

    expect(error.retryAfterSeconds).toBe(45);
    expect(error.requestId).toBe("hdr-only");
  });

  it("handles non-envelope bodies", () => {
    const error = parseErrorResponse(500, "boom");
    expect(error.code).toBe("UNKNOWN_ERROR");
    expect(error.message).toBe("boom");
  });
});

describe("ApiClientError", () => {
  it("exposes typed fields and type guard", () => {
    const err = new ApiClientError({
      status: 403,
      code: "FORBIDDEN",
      message: "Nope",
      requestId: "r1",
    });

    expect(err).toBeInstanceOf(Error);
    expect(err.name).toBe("ApiClientError");
    expect(err.status).toBe(403);
    expect(isApiClientError(err)).toBe(true);
    expect(isApiClientError(new Error("x"))).toBe(false);
  });
});

describe("shouldRetryStatus", () => {
  it("retries only temporary upstream failures", () => {
    expect(shouldRetryStatus(503)).toBe(true);
    expect(shouldRetryStatus(502)).toBe(true);
    expect(shouldRetryStatus(504)).toBe(true);
  });

  it("does not retry client or auth errors", () => {
    for (const status of [401, 403, 404, 409, 422, 429, 400]) {
      expect(shouldRetryStatus(status)).toBe(false);
    }
  });
});
