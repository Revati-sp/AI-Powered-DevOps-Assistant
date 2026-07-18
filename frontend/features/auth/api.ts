import { ApiClientError, parseErrorResponse } from "@/lib/api/errors";
import type { components } from "@/lib/api/generated-types";
import type { LoginFormValues, RegisterFormValues } from "@/features/auth/schemas";

export type UserResponse = components["schemas"]["UserResponse"];

export type LoginSuccess = {
  success: true;
  expires_in: number;
};

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

function throwFromResponse(status: number, json: unknown, headers: Headers): never {
  throw new ApiClientError(parseErrorResponse(status, json, headers));
}

export async function loginRequest(values: LoginFormValues): Promise<LoginSuccess> {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(values),
    credentials: "include",
  });

  const json = await parseJsonSafe(response);
  if (!response.ok) {
    throwFromResponse(response.status, json, response.headers);
  }

  return json as LoginSuccess;
}

export async function registerRequest(values: RegisterFormValues): Promise<UserResponse> {
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(values),
    credentials: "include",
  });

  const json = await parseJsonSafe(response);
  if (!response.ok) {
    throwFromResponse(response.status, json, response.headers);
  }

  const envelope = json as { data?: UserResponse } | null;
  if (envelope && typeof envelope === "object" && "data" in envelope) {
    return envelope.data as UserResponse;
  }
  return json as UserResponse;
}

export async function logoutRequest(): Promise<void> {
  const response = await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    const json = await parseJsonSafe(response);
    throwFromResponse(response.status, json, response.headers);
  }
}

export async function logoutAllRequest(): Promise<void> {
  const response = await fetch("/api/auth/logout-all", {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    const json = await parseJsonSafe(response);
    throwFromResponse(response.status, json, response.headers);
  }
}

export async function fetchCurrentUser(): Promise<UserResponse | null> {
  const response = await fetch("/api/auth/me", {
    method: "GET",
    credentials: "include",
    cache: "no-store",
  });

  if (response.status === 401) {
    return null;
  }

  const json = await parseJsonSafe(response);
  if (!response.ok) {
    throwFromResponse(response.status, json, response.headers);
  }

  const envelope = json as { data?: UserResponse } | null;
  if (envelope && typeof envelope === "object" && "data" in envelope) {
    return envelope.data ?? null;
  }
  return json as UserResponse;
}
