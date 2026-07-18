export type ApiError = {
  status: number;
  code: string;
  message: string;
  details?: unknown;
  requestId?: string;
  retryAfterSeconds?: number;
};

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: unknown;
  readonly requestId?: string;
  readonly retryAfterSeconds?: number;

  constructor(error: ApiError) {
    super(error.message);
    this.name = "ApiClientError";
    this.status = error.status;
    this.code = error.code;
    this.details = error.details;
    this.requestId = error.requestId;
    this.retryAfterSeconds = error.retryAfterSeconds;
  }
}

export function isApiClientError(e: unknown): e is ApiClientError {
  return e instanceof ApiClientError;
}

type ErrorEnvelope = {
  success?: boolean;
  error?: {
    code?: unknown;
    message?: unknown;
    details?: unknown;
  };
  message?: unknown;
  code?: unknown;
  detail?: unknown;
};

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value !== null && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

function readString(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function readRetryAfterSeconds(details: unknown, headers?: Headers): number | undefined {
  const detailRecord = asRecord(details);
  const fromDetails = detailRecord?.retry_after_seconds;
  if (typeof fromDetails === "number" && Number.isFinite(fromDetails)) {
    return fromDetails;
  }
  if (typeof fromDetails === "string" && fromDetails.trim() !== "") {
    const parsed = Number(fromDetails);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  const headerValue = headers?.get("Retry-After");
  if (headerValue) {
    const parsed = Number(headerValue);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return undefined;
}

function readRequestId(details: unknown, headers?: Headers): string | undefined {
  const detailRecord = asRecord(details);
  const fromDetails = readString(detailRecord?.request_id);
  if (fromDetails) {
    return fromDetails;
  }
  return readString(headers?.get("X-Request-ID") ?? undefined);
}

/**
 * Parse a backend ErrorResponse envelope (or best-effort fallbacks).
 */
export function parseErrorResponse(status: number, body: unknown, headers?: Headers): ApiError {
  const envelope = asRecord(body) as ErrorEnvelope | null;
  const errorObject = asRecord(envelope?.error);

  const code =
    readString(errorObject?.code) ??
    readString(envelope?.code) ??
    (status === 401
      ? "UNAUTHORIZED"
      : status === 403
        ? "FORBIDDEN"
        : status === 404
          ? "NOT_FOUND"
          : status === 429
            ? "RATE_LIMITED"
            : "UNKNOWN_ERROR");

  const message =
    readString(errorObject?.message) ??
    readString(envelope?.message) ??
    readString(envelope?.detail) ??
    (typeof body === "string" && body.trim() !== ""
      ? body
      : `Request failed with status ${status}`);

  const details = errorObject?.details ?? undefined;

  return {
    status,
    code,
    message,
    details,
    requestId: readRequestId(details, headers),
    retryAfterSeconds: readRetryAfterSeconds(details, headers),
  };
}

/**
 * Statuses safe to retry at the query/client layer.
 * Do not retry auth, permission, conflict, validation, or rate-limit responses.
 */
export function shouldRetryStatus(status: number): boolean {
  return status === 503 || status === 502 || status === 504;
}
