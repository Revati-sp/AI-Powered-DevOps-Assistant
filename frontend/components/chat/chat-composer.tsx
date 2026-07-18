"use client";

import * as React from "react";
import { SendHorizontal, Square } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { chatComposerSchema } from "@/features/chat/schemas";
import { CHAT_MESSAGE_MAX, LLM_PROVIDERS, type LlmProvider } from "@/lib/constants/app";
import { cn } from "@/lib/utils/cn";

export type ChatComposerSubmit = {
  message: string;
  provider: LlmProvider;
};

type ChatComposerProps = {
  provider: LlmProvider;
  onProviderChange: (provider: LlmProvider) => void;
  onSubmit: (values: ChatComposerSubmit) => void;
  onStop?: () => void;
  isBusy?: boolean;
  disabled?: boolean;
  initialMessage?: string;
  className?: string;
};

export function ChatComposer({
  provider,
  onProviderChange,
  onSubmit,
  onStop,
  isBusy = false,
  disabled = false,
  initialMessage = "",
  className,
}: ChatComposerProps) {
  const [message, setMessage] = React.useState(initialMessage);
  const [error, setError] = React.useState<string | null>(null);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const [prevInitial, setPrevInitial] = React.useState(initialMessage);

  if (initialMessage !== prevInitial) {
    setPrevInitial(initialMessage);
    setMessage(initialMessage);
  }

  const charCount = message.length;
  const overLimit = charCount > CHAT_MESSAGE_MAX;

  function handleSubmit() {
    if (isBusy || disabled) {
      return;
    }
    const parsed = chatComposerSchema.safeParse({
      message,
      provider,
    });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid message");
      return;
    }
    setError(null);
    onSubmit(parsed.data);
    setMessage("");
    textareaRef.current?.focus();
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div
      className={cn(
        "border-border bg-card/80 space-y-3 rounded-xl border p-3 shadow-sm backdrop-blur",
        className,
      )}
    >
      <Textarea
        ref={textareaRef}
        value={message}
        onChange={(event) => {
          setMessage(event.target.value);
          if (error) {
            setError(null);
          }
        }}
        onKeyDown={handleKeyDown}
        placeholder="Ask about infrastructure, logs, or pipelines…"
        disabled={disabled || isBusy}
        rows={3}
        className="min-h-[84px] resize-none border-0 bg-transparent shadow-none focus-visible:ring-0"
        aria-label="Chat message"
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Label htmlFor="chat-provider" className="text-muted-foreground text-xs">
              Provider
            </Label>
            <Select
              value={provider}
              onValueChange={(value) => onProviderChange(value as LlmProvider)}
              disabled={disabled || isBusy}
            >
              <SelectTrigger id="chat-provider" className="h-8 w-[130px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LLM_PROVIDERS.map((item) => (
                  <SelectItem key={item} value={item} className="capitalize">
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <span
            className={cn(
              "text-muted-foreground text-xs tabular-nums",
              overLimit && "text-destructive",
            )}
          >
            {charCount}/{CHAT_MESSAGE_MAX}
          </span>
        </div>

        {isBusy ? (
          <Button type="button" variant="destructive" size="sm" onClick={onStop}>
            <Square className="h-3.5 w-3.5" />
            Stop
          </Button>
        ) : (
          <Button
            type="button"
            size="sm"
            onClick={handleSubmit}
            disabled={disabled || !message.trim() || overLimit}
          >
            <SendHorizontal className="h-3.5 w-3.5" />
            Send
          </Button>
        )}
      </div>

      {error ? (
        <p className="text-destructive text-xs" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
