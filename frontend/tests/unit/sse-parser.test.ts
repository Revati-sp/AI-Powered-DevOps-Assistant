import { describe, expect, it } from "vitest";
import { parseChatSseData } from "@/lib/sse/chat-stream";
import { createSseParser } from "@/lib/sse/parse-sse";

describe("createSseParser", () => {
  it("parses a complete event block", () => {
    const parser = createSseParser();
    const events = parser.push('event: token\ndata: {"content":"hi"}\n\n');
    expect(events).toEqual([{ event: "token", data: '{"content":"hi"}' }]);
  });

  it("handles fragmented chunks across pushes", () => {
    const parser = createSseParser();
    expect(parser.push("event: conve")).toEqual([]);
    expect(parser.push('rsation\ndata: {"conversation_id":"')).toEqual([]);
    expect(parser.push('abc"}\n\nevent: token\ndata: {"content":"Hel')).toEqual([
      { event: "conversation", data: '{"conversation_id":"abc"}' },
    ]);
    expect(parser.push('lo"}\n\n')).toEqual([{ event: "token", data: '{"content":"Hello"}' }]);
  });

  it("supports multiple events in one chunk and multi-line data", () => {
    const parser = createSseParser();
    const events = parser.push(
      [
        "event: token",
        "data: line1",
        "data: line2",
        "",
        "event: heartbeat",
        'data: {"status":"active"}',
        "",
        "id: 42",
        "event: completed",
        'data: {"message_id":"m1","provider":"gemini"}',
        "",
        "",
      ].join("\n"),
    );

    expect(events).toHaveLength(3);
    expect(events[0]).toEqual({ event: "token", data: "line1\nline2" });
    expect(events[1]).toEqual({
      event: "heartbeat",
      data: '{"status":"active"}',
    });
    expect(events[2]).toEqual({
      event: "completed",
      data: '{"message_id":"m1","provider":"gemini"}',
      id: "42",
    });
  });

  it("ignores comment lines and flushes trailing buffered event", () => {
    const parser = createSseParser();
    expect(parser.push(": keep-alive\n")).toEqual([]);
    expect(parser.push('event: error\ndata: {"code":"X","message":"y"}')).toEqual([]);
    expect(parser.flush()).toEqual([{ event: "error", data: '{"code":"X","message":"y"}' }]);
  });
});

describe("parseChatSseData", () => {
  it("maps backend chat stream event shapes", () => {
    expect(
      parseChatSseData({
        event: "conversation",
        data: '{"conversation_id":"c1"}',
      }),
    ).toEqual({
      type: "conversation",
      data: { conversation_id: "c1" },
    });

    expect(parseChatSseData({ event: "token", data: '{"content":"x"}' })).toEqual({
      type: "token",
      data: { content: "x" },
    });

    expect(
      parseChatSseData({
        event: "heartbeat",
        data: '{"status":"active"}',
      }),
    ).toEqual({ type: "heartbeat", data: { status: "active" } });

    expect(
      parseChatSseData({
        event: "completed",
        data: '{"message_id":"m","provider":"llama"}',
      }),
    ).toEqual({
      type: "completed",
      data: { message_id: "m", provider: "llama" },
    });

    expect(
      parseChatSseData({
        event: "error",
        data: '{"code":"LLM_STREAM_ERROR","message":"fail"}',
      }),
    ).toEqual({
      type: "error",
      data: { code: "LLM_STREAM_ERROR", message: "fail" },
    });
  });
});
