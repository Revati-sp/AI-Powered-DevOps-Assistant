import type { SseEvent } from "@/lib/sse/parse-sse";

export type ChatConversationEvent = {
  conversation_id: string;
};

export type ChatTokenEvent = {
  content: string;
};

export type ChatHeartbeatEvent = {
  status: string;
};

export type ChatCompletedEvent = {
  message_id: string;
  provider: string;
};

export type ChatErrorEvent = {
  code: string;
  message: string;
};

export type ParsedChatSseEvent =
  | { type: "conversation"; data: ChatConversationEvent }
  | { type: "token"; data: ChatTokenEvent }
  | { type: "heartbeat"; data: ChatHeartbeatEvent }
  | { type: "completed"; data: ChatCompletedEvent }
  | { type: "error"; data: ChatErrorEvent }
  | { type: "unknown"; event: string; data: unknown };

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value !== null && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

function parseJsonData(raw: string): unknown {
  if (raw === "") {
    return null;
  }
  try {
    return JSON.parse(raw) as unknown;
  } catch {
    return raw;
  }
}

/**
 * Map a raw SSE event from `/chat/stream` onto typed chat payloads.
 * Heartbeats should be ignored by UI consumers.
 */
export function parseChatSseData(event: SseEvent): ParsedChatSseEvent {
  const payload = parseJsonData(event.data);
  const record = asRecord(payload);

  switch (event.event) {
    case "conversation": {
      const conversationId = record?.conversation_id;
      if (typeof conversationId === "string") {
        return {
          type: "conversation",
          data: { conversation_id: conversationId },
        };
      }
      break;
    }
    case "token": {
      const content = record?.content;
      if (typeof content === "string") {
        return { type: "token", data: { content } };
      }
      break;
    }
    case "heartbeat": {
      const status = typeof record?.status === "string" ? record.status : "active";
      return { type: "heartbeat", data: { status } };
    }
    case "completed": {
      const messageId = record?.message_id;
      const provider = record?.provider;
      if (typeof messageId === "string" && typeof provider === "string") {
        return {
          type: "completed",
          data: { message_id: messageId, provider },
        };
      }
      break;
    }
    case "error": {
      const code = typeof record?.code === "string" ? record.code : "LLM_STREAM_ERROR";
      const message =
        typeof record?.message === "string"
          ? record.message
          : "The AI response could not be completed.";
      return { type: "error", data: { code, message } };
    }
    default:
      break;
  }

  return { type: "unknown", event: event.event, data: payload };
}
