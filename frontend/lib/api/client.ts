import { ApiClientError, parseErrorResponse } from "@/lib/api/errors";

export type RequestOptions = {
  method?: string;
  body?: unknown;
  formData?: FormData;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeoutMs?: number;
  /** Server-side only — never log or expose this value. */
  accessToken?: string;
  /** Skip APIResponse envelope unwrap (login/refresh token pairs, raw payloads). */
  raw?: boolean;
  /** application/x-www-form-urlencoded body (OAuth2 password login). */
  formUrlEncoded?: URLSearchParams;
};

type ApiSuccessEnvelope<T> = {
  success?: boolean;
  data?: T;
  message?: string | null;
};

export function getApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return (
      process.env.INTERNAL_API_BASE_URL ||
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      "http://localhost:8000"
    );
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL || "";
}

function resolveRequestUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (typeof window === "undefined") {
    const base = getApiBaseUrl().replace(/\/$/, "");
    return `${base}${normalized}`;
  }
  // Browser traffic goes through the Next.js BFF (HTTP-only cookies).
  return `/api/bff${normalized}`;
}

export function unwrapData<T>(json: unknown): T {
  if (json !== null && typeof json === "object" && "data" in json) {
    return (json as ApiSuccessEnvelope<T>).data as T;
  }
  return json as T;
}

function mergeSignals(
  external: AbortSignal | undefined,
  timeoutMs: number | undefined,
): { signal: AbortSignal | undefined; cleanup: () => void } {
  if (timeoutMs === undefined || timeoutMs <= 0) {
    return { signal: external, cleanup: () => undefined };
  }

  const controller = new AbortController();
  const timer = setTimeout(() => {
    controller.abort(new DOMException("Request timed out", "TimeoutError"));
  }, timeoutMs);

  const onAbort = () => {
    controller.abort(external?.reason);
  };
  external?.addEventListener("abort", onAbort);

  return {
    signal: controller.signal,
    cleanup: () => {
      clearTimeout(timer);
      external?.removeEventListener("abort", onAbort);
    },
  };
}

async function parseJsonSafe(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

/**
 * Typed fetch against FastAPI (server) or `/api/bff` (browser).
 * Never logs tokens or Authorization headers.
 */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = "GET",
    body,
    formData,
    headers: extraHeaders,
    signal,
    timeoutMs = 30_000,
    accessToken,
    raw = false,
    formUrlEncoded,
  } = options;

  const headers: Record<string, string> = { ...extraHeaders };
  const init: RequestInit = {
    method,
    credentials: typeof window === "undefined" ? "omit" : "include",
  };

  if (typeof window === "undefined" && accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  if (formData) {
    init.body = formData;
    // Let the runtime set multipart boundary — do not set Content-Type.
  } else if (formUrlEncoded) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    init.body = formUrlEncoded.toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }

  init.headers = headers;

  const { signal: mergedSignal, cleanup } = mergeSignals(signal, timeoutMs);
  if (mergedSignal) {
    init.signal = mergedSignal;
  }

  try {
    const response = await fetch(resolveRequestUrl(path), init);
    const json = await parseJsonSafe(response);

    if (!response.ok) {
      throw new ApiClientError(parseErrorResponse(response.status, json, response.headers));
    }

    if (raw) {
      return json as T;
    }

    const envelope = json as ApiSuccessEnvelope<T> | null;
    if (
      envelope &&
      typeof envelope === "object" &&
      "success" in envelope &&
      envelope.success === false
    ) {
      throw new ApiClientError(parseErrorResponse(response.status, json, response.headers));
    }

    return unwrapData<T>(json);
  } finally {
    cleanup();
  }
}
