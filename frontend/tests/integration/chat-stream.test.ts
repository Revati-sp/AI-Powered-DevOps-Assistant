import { afterEach, describe, expect, it, vi } from "vitest";

import { parseChatSseData } from "@/lib/sse/chat-stream";
import { createSseParser } from "@/lib/sse/parse-sse";

/**
 * Integration-style coverage for fragmented SSE over a mocked fetch stream,
 * mirroring browser consumption of `/api/bff/api/v1/chat/stream`.
 */
async function consumeChatStream(response: Response) {
  if (!response.ok || !response.body) {
    throw new Error(`Stream failed: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const parser = createSseParser();
  const tokens: string[] = [];
  let conversationId: string | null = null;
  let completed: { message_id: string; provider: string } | null = null;
  let error: { code: string; message: string } | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    for (const event of parser.push(decoder.decode(value, { stream: true }))) {
      const parsed = parseChatSseData(event);
      if (parsed.type === "conversation") {
        conversationId = parsed.data.conversation_id;
      } else if (parsed.type === "token") {
        tokens.push(parsed.data.content);
      } else if (parsed.type === "completed") {
        completed = parsed.data;
      } else if (parsed.type === "error") {
        error = parsed.data;
      }
    }
  }

  for (const event of parser.flush()) {
    const parsed = parseChatSseData(event);
    if (parsed.type === "token") {
      tokens.push(parsed.data.content);
    } else if (parsed.type === "completed") {
      completed = parsed.data;
    } else if (parsed.type === "error") {
      error = parsed.data;
    } else if (parsed.type === "conversation") {
      conversationId = parsed.data.conversation_id;
    }
  }

  return {
    conversationId,
    text: tokens.join(""),
    completed,
    error,
  };
}

function streamFromChunks(chunks: string[], status = 200) {
  const encoder = new TextEncoder();
  let index = 0;
  return new Response(
    new ReadableStream({
      pull(controller) {
        if (index >= chunks.length) {
          controller.close();
          return;
        }
        controller.enqueue(encoder.encode(chunks[index]));
        index += 1;
      },
    }),
    {
      status,
      headers: { "Content-Type": "text/event-stream" },
    },
  );
}

describe("chat stream integration", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("parses a fragmented SSE stream via mocked fetch", async () => {
    const chunks = [
      "event: conversati",
      'on\ndata: {"conversation_id":"conv-1"}\n\n',
      'event: token\ndata: {"content":"Hel"}\n\n: heartbeat\n\n',
      'event: token\ndata: {"content":"lo"}\n\nevent: heart',
      'beat\ndata: {"status":"active"}\n\n',
      'event: completed\ndata: {"message_id":"msg-9","provider":"gemini"}\n\n',
    ];

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => streamFromChunks(chunks)),
    );

    const response = await fetch("/api/bff/api/v1/chat/stream", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({
        message: "hi",
        provider: "gemini",
      }),
    });

    const result = await consumeChatStream(response);

    expect(fetch).toHaveBeenCalledWith(
      "/api/bff/api/v1/chat/stream",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
    expect(result.conversationId).toBe("conv-1");
    expect(result.text).toBe("Hello");
    expect(result.completed).toEqual({
      message_id: "msg-9",
      provider: "gemini",
    });
    expect(result.error).toBeNull();
  });

  it("surfaces stream error events without retrying", async () => {
    const chunks = [
      'event: conversation\ndata: {"conversation_id":"c2"}\n\n',
      'event: token\ndata: {"content":"partial"}\n\n',
      'event: error\ndata: {"code":"LLM_STREAM_ERROR","message":"Provider failed"}\n\n',
    ];

    const result = await consumeChatStream(streamFromChunks(chunks));

    expect(result.text).toBe("partial");
    expect(result.error).toEqual({
      code: "LLM_STREAM_ERROR",
      message: "Provider failed",
    });
    expect(result.completed).toBeNull();
  });
});
