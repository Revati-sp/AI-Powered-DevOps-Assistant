import { ApiClientError, type ApiError, parseErrorResponse } from "@/lib/api/errors";
import { parseChatSseData } from "@/lib/sse/chat-stream";
import type { createSseParser } from "@/lib/sse/parse-sse";

export function toStreamApiError(error: unknown): ApiError {
  if (error instanceof ApiClientError) {
    return {
      status: error.status,
      code: error.code,
      message: error.message,
      details: error.details,
      requestId: error.requestId,
      retryAfterSeconds: error.retryAfterSeconds,
    };
  }
  if (error instanceof DOMException && error.name === "AbortError") {
    return {
      status: 0,
      code: "ABORTED",
      message: "Request was cancelled.",
    };
  }
  return {
    status: 0,
    code: "UNKNOWN_ERROR",
    message:
      error instanceof Error && error.message
        ? error.message
        : "Something went wrong while streaming the response.",
  };
}

export async function throwIfStreamHttpError(response: Response): Promise<void> {
  if (response.ok) {
    return;
  }
  const text = await response.text();
  let body: unknown = text;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = text;
  }
  throw new ApiClientError(parseErrorResponse(response.status, body, response.headers));
}

export type StreamTerminal =
  | { kind: "completed"; messageId: string; provider: string }
  | { kind: "error"; error: ApiError }
  | null;

export function applyParsedStreamEvent(
  parsed: ReturnType<typeof parseChatSseData>,
  handlers: {
    onConversation: (conversationId: string) => void;
    onToken: (content: string) => void;
  },
): StreamTerminal {
  switch (parsed.type) {
    case "heartbeat":
    case "unknown":
      return null;
    case "conversation":
      handlers.onConversation(parsed.data.conversation_id);
      return null;
    case "token":
      handlers.onToken(parsed.data.content);
      return null;
    case "completed":
      return {
        kind: "completed",
        messageId: parsed.data.message_id,
        provider: parsed.data.provider,
      };
    case "error":
      return {
        kind: "error",
        error: {
          status: 0,
          code: parsed.data.code,
          message: parsed.data.message,
        },
      };
    default:
      return null;
  }
}

export async function readChatSseBody(
  body: ReadableStream<Uint8Array>,
  parser: ReturnType<typeof createSseParser>,
  handlers: {
    onConversation: (conversationId: string) => void;
    onToken: (content: string) => void;
  },
): Promise<StreamTerminal> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let terminal: StreamTerminal = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    for (const event of parser.push(decoder.decode(value, { stream: true }))) {
      const next = applyParsedStreamEvent(parseChatSseData(event), handlers);
      if (next) {
        terminal = next;
        break;
      }
    }

    if (terminal) {
      break;
    }
  }

  for (const event of parser.flush()) {
    const next = applyParsedStreamEvent(parseChatSseData(event), handlers);
    if (next) {
      terminal = next;
    }
  }

  return terminal;
}
