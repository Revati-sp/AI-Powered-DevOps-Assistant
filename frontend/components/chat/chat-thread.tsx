"use client";

import * as React from "react";

import { ChatEmptyState } from "@/components/chat/chat-empty-state";
import { ChatMessage } from "@/components/chat/chat-message";
import { ErrorState } from "@/components/feedback/error-state";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatMessageView } from "@/features/chat/types";
import type { ApiError } from "@/lib/api/errors";
import { cn } from "@/lib/utils/cn";

type ChatThreadProps = {
  messages: ChatMessageView[];
  streamingContent?: string;
  isStreaming?: boolean;
  streamProvider?: string | null;
  error?: ApiError | null;
  onRetry?: () => void;
  onSuggestion?: (prompt: string) => void;
  className?: string;
};

export function ChatThread({
  messages,
  streamingContent = "",
  isStreaming = false,
  streamProvider,
  error,
  onRetry,
  onSuggestion,
  className,
}: ChatThreadProps) {
  const bottomRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, streamingContent, isStreaming, error]);

  const displayMessages = React.useMemo(() => {
    if (!isStreaming && !streamingContent) {
      return messages;
    }
    const streamingMessage: ChatMessageView = {
      id: "streaming-assistant",
      role: "assistant",
      content: streamingContent,
      createdAt: new Date().toISOString(),
      provider: streamProvider,
      isStreaming,
    };
    return [...messages, streamingMessage];
  }, [isStreaming, messages, streamProvider, streamingContent]);

  if (displayMessages.length === 0 && !error) {
    return (
      <div className={cn("flex h-full items-center justify-center", className)}>
        <ChatEmptyState onSuggestion={onSuggestion} />
      </div>
    );
  }

  return (
    <ScrollArea className={cn("h-full", className)}>
      <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-6">
        {displayMessages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {error ? (
          <div className="border-destructive/30 bg-destructive/5 rounded-xl border">
            <ErrorState
              className="py-8"
              title={error.code === "RATE_LIMITED" ? "Rate limit reached" : "Response failed"}
              message={
                error.code === "RATE_LIMITED" && error.retryAfterSeconds
                  ? `${error.message} Try again in ${error.retryAfterSeconds}s.`
                  : error.message
              }
              requestId={error.requestId}
              onRetry={onRetry}
            />
          </div>
        ) : null}

        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
