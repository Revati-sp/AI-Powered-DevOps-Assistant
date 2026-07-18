"use client";

import * as React from "react";

import type { StreamingChatStatus } from "@/features/chat/types";
import { ApiClientError, type ApiError } from "@/lib/api/errors";
import { endpoints } from "@/lib/api/endpoints";
import { createSseParser } from "@/lib/sse/parse-sse";
import {
  readChatSseBody,
  throwIfStreamHttpError,
  toStreamApiError,
} from "@/hooks/streaming-chat-utils";

const TOKEN_FLUSH_MS = 50;

export type StartStreamingChatInput = {
  message: string;
  conversationId?: string | null;
  organizationId?: string | null;
  provider: string;
};

export type StreamingChatState = {
  status: StreamingChatStatus;
  tokens: string;
  conversationId: string | null;
  error: ApiError | null;
  provider: string | null;
  messageId: string | null;
};

const initialState: StreamingChatState = {
  status: "idle",
  tokens: "",
  conversationId: null,
  error: null,
  provider: null,
  messageId: null,
};

export function useStreamingChat() {
  const [state, setState] = React.useState<StreamingChatState>(initialState);
  const abortRef = React.useRef<AbortController | null>(null);
  const tokenBufferRef = React.useRef("");
  const flushTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const rafRef = React.useRef<number | null>(null);

  const clearFlushTimers = React.useCallback(() => {
    if (flushTimerRef.current !== null) {
      clearTimeout(flushTimerRef.current);
      flushTimerRef.current = null;
    }
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const flushTokens = React.useCallback(() => {
    clearFlushTimers();
    const next = tokenBufferRef.current;
    setState((prev) => (prev.tokens === next ? prev : { ...prev, tokens: next }));
  }, [clearFlushTimers]);

  const scheduleTokenFlush = React.useCallback(() => {
    if (flushTimerRef.current !== null || rafRef.current !== null) {
      return;
    }
    const run = () => {
      flushTimerRef.current = setTimeout(() => {
        flushTimerRef.current = null;
        flushTokens();
      }, TOKEN_FLUSH_MS);
    };
    if (typeof requestAnimationFrame === "function") {
      rafRef.current = requestAnimationFrame(() => {
        rafRef.current = null;
        run();
      });
      return;
    }
    run();
  }, [flushTokens]);

  const stop = React.useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    clearFlushTimers();
    setState((prev) => {
      if (prev.status !== "sending" && prev.status !== "streaming") {
        return prev;
      }
      return {
        ...prev,
        status: "cancelled",
        tokens: tokenBufferRef.current,
      };
    });
  }, [clearFlushTimers]);

  const reset = React.useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    clearFlushTimers();
    tokenBufferRef.current = "";
    setState(initialState);
  }, [clearFlushTimers]);

  const start = React.useCallback(
    async (input: StartStreamingChatInput) => {
      abortRef.current?.abort();
      clearFlushTimers();
      tokenBufferRef.current = "";

      const controller = new AbortController();
      abortRef.current = controller;

      setState({
        status: "sending",
        tokens: "",
        conversationId: input.conversationId ?? null,
        error: null,
        provider: input.provider,
        messageId: null,
      });

      try {
        const response = await fetch(`/api/bff${endpoints.chat.stream()}`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify({
            message: input.message,
            conversation_id: input.conversationId ?? null,
            organization_id: input.organizationId ?? null,
            provider: input.provider,
          }),
          signal: controller.signal,
        });

        await throwIfStreamHttpError(response);

        if (!response.body) {
          throw new ApiClientError({
            status: response.status,
            code: "STREAM_UNAVAILABLE",
            message: "Streaming response body was empty.",
          });
        }

        setState((prev) => ({ ...prev, status: "streaming" }));

        const terminal = await readChatSseBody(response.body, createSseParser(), {
          onConversation: (conversationId) => {
            setState((prev) => ({ ...prev, conversationId }));
          },
          onToken: (content) => {
            tokenBufferRef.current += content;
            scheduleTokenFlush();
          },
        });

        clearFlushTimers();
        const finalTokens = tokenBufferRef.current;

        if (controller.signal.aborted) {
          setState((prev) => ({
            ...prev,
            status: "cancelled",
            tokens: finalTokens,
          }));
          return;
        }

        if (terminal?.kind === "error") {
          setState((prev) => ({
            ...prev,
            status: "error",
            tokens: finalTokens,
            error: terminal.error,
          }));
          return;
        }

        if (terminal?.kind === "completed") {
          setState((prev) => ({
            ...prev,
            status: "completed",
            tokens: finalTokens,
            provider: terminal.provider,
            messageId: terminal.messageId,
            error: null,
          }));
          return;
        }

        setState((prev) => ({
          ...prev,
          status: "error",
          tokens: finalTokens,
          error: {
            status: 0,
            code: "STREAM_INCOMPLETE",
            message: "The stream ended before the response completed.",
          },
        }));
      } catch (error) {
        clearFlushTimers();
        if (controller.signal.aborted) {
          setState((prev) => ({
            ...prev,
            status: "cancelled",
            tokens: tokenBufferRef.current,
          }));
          return;
        }
        setState((prev) => ({
          ...prev,
          status: "error",
          tokens: tokenBufferRef.current,
          error: toStreamApiError(error),
        }));
      } finally {
        if (abortRef.current === controller) {
          abortRef.current = null;
        }
      }
    },
    [clearFlushTimers, scheduleTokenFlush],
  );

  React.useEffect(() => {
    return () => {
      abortRef.current?.abort();
      clearFlushTimers();
    };
  }, [clearFlushTimers]);

  return {
    ...state,
    start,
    stop,
    reset,
    isBusy: state.status === "sending" || state.status === "streaming",
  };
}
