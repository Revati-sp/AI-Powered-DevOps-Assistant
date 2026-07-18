import { ApiClientError, parseErrorResponse } from "@/lib/api/errors";
import type { components } from "@/lib/api/generated-types";
import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type {
  ChangePasswordFormValues,
  ForgotPasswordFormValues,
  LoginFormValues,
  RegisterFormValues,
  ResetPasswordFormValues,
} from "@/features/auth/schemas";
import type {
  ForgotPasswordResponse,
  InvitationAcceptResponse,
  SessionResponse,
} from "@/features/auth/types";

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

function unwrapEnvelopeData<T>(json: unknown): T {
  const envelope = json as { data?: T } | null;
  if (envelope && typeof envelope === "object" && "data" in envelope) {
    return envelope.data as T;
  }
  return json as T;
}

async function authRouteFetch<T>(
  path: string,
  options: { method?: string; body?: unknown } = {},
): Promise<T> {
  const response = await fetch(path, {
    method: options.method ?? "GET",
    headers:
      options.body !== undefined
        ? { "Content-Type": "application/json", Accept: "application/json" }
        : { Accept: "application/json" },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    credentials: "include",
  });

  const json = await parseJsonSafe(response);
  if (!response.ok) {
    throwFromResponse(response.status, json, response.headers);
  }

  return unwrapEnvelopeData<T>(json);
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

  return unwrapEnvelopeData<UserResponse>(json);
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

  return unwrapEnvelopeData<UserResponse>(json);
}

export async function forgotPasswordRequest(
  values: ForgotPasswordFormValues,
): Promise<ForgotPasswordResponse> {
  return authRouteFetch<ForgotPasswordResponse>("/api/auth/forgot-password", {
    method: "POST",
    body: values,
  });
}

export async function resetPasswordRequest(
  token: string,
  values: ResetPasswordFormValues,
): Promise<void> {
  await authRouteFetch<null>("/api/auth/reset-password", {
    method: "POST",
    body: {
      token,
      new_password: values.new_password,
    },
  });
}

export async function verifyEmailRequest(token: string): Promise<UserResponse> {
  return authRouteFetch<UserResponse>("/api/auth/verify-email", {
    method: "POST",
    body: { token },
  });
}

export async function sendVerificationRequest(): Promise<void> {
  await authRouteFetch<null>("/api/auth/send-verification", {
    method: "POST",
  });
}

export async function changePasswordRequest(
  values: Pick<ChangePasswordFormValues, "current_password" | "new_password">,
): Promise<void> {
  await authRouteFetch<null>("/api/auth/change-password", {
    method: "POST",
    body: values,
  });
}

export async function listSessionsRequest(): Promise<SessionResponse[]> {
  return authRouteFetch<SessionResponse[]>("/api/auth/sessions");
}

export async function revokeSessionRequest(sessionId: string): Promise<void> {
  await authRouteFetch<null>(`/api/auth/sessions/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
}

export async function acceptInvitationRequest(
  token: string,
): Promise<InvitationAcceptResponse> {
  return apiFetch<InvitationAcceptResponse>(endpoints.invitations.accept(), {
    method: "POST",
    body: { token },
  });
}

export async function declineInvitationRequest(token: string): Promise<void> {
  await apiFetch<void>(endpoints.invitations.decline(), {
    method: "POST",
    body: { token },
  });
}
