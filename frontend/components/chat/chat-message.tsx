"use client";

import { Bot, User } from "lucide-react";

import { ProviderBadge } from "@/components/chat/provider-badge";
import { CopyButton } from "@/components/data-display/copy-button";
import { MarkdownRenderer } from "@/components/data-display/markdown-renderer";
import type { ChatMessageView } from "@/features/chat/types";
import { formatDateTime } from "@/lib/formatters/date";
import { cn } from "@/lib/utils/cn";

export function ChatMessage({ message }: { message: ChatMessageView }) {
  const isUser = message.role === "user";

  return (
    <article className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-primary text-primary-foreground" : "bg-primary/10 text-primary",
        )}
      >
        {isUser ? (
          <User className="h-4 w-4" aria-hidden />
        ) : (
          <Bot className="h-4 w-4" aria-hidden />
        )}
      </div>

      <div
        className={cn(
          "max-w-[min(100%,42rem)] min-w-0 space-y-2",
          isUser ? "items-end text-right" : "items-start",
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm",
            isUser ? "bg-primary text-primary-foreground" : "bg-muted/60 border-border border",
          )}
        >
          {isUser ? (
            <p className="text-left break-words whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="text-left">
              {message.content ? (
                <MarkdownRenderer content={message.content} />
              ) : message.isStreaming ? (
                <span className="text-muted-foreground">Thinking…</span>
              ) : null}
              {message.isStreaming ? (
                <span
                  className="bg-primary ml-0.5 inline-block h-4 w-1.5 animate-pulse align-middle"
                  aria-hidden
                />
              ) : null}
            </div>
          )}
        </div>

        <div
          className={cn(
            "text-muted-foreground flex items-center gap-2 text-xs",
            isUser ? "justify-end" : "justify-start",
          )}
        >
          {message.provider ? <ProviderBadge provider={message.provider} /> : null}
          <time dateTime={message.createdAt}>{formatDateTime(message.createdAt)}</time>
          {!isUser && message.content ? (
            <CopyButton value={message.content} className="h-7 w-7" />
          ) : null}
        </div>
      </div>
    </article>
  );
}
