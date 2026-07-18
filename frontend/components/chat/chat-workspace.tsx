"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { PanelLeft } from "lucide-react";

import { ChatComposer } from "@/components/chat/chat-composer";
import { ChatThread } from "@/components/chat/chat-thread";
import { ConversationSidebar } from "@/components/chat/conversation-sidebar";
import { ErrorState } from "@/components/feedback/error-state";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { getConversation } from "@/features/chat/api";
import type { ChatMessageView } from "@/features/chat/types";
import { useStreamingChat } from "@/hooks/use-streaming-chat";
import { isApiClientError } from "@/lib/api/errors";
import { queryKeys } from "@/lib/api/query-keys";
import type { LlmProvider } from "@/lib/constants/app";
import { useWorkspaceStore } from "@/store/workspace-store";

function newId(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

function asProvider(value: string | undefined): LlmProvider | null {
  if (value === "gemini" || value === "llama" || value === "mistral") {
    return value;
  }
  return null;
}

export function ChatWorkspace({ conversationId }: { conversationId?: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const stream = useStreamingChat();

  const [providerOverride, setProviderOverride] = React.useState<LlmProvider | null>(null);
  const [draftMessages, setDraftMessages] = React.useState<ChatMessageView[]>([]);
  const [pendingRetry, setPendingRetry] = React.useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [activeConversationId, setActiveConversationId] = React.useState(conversationId);
  const [committedStreamKey, setCommittedStreamKey] = React.useState<string | null>(null);
  const navigatedRef = React.useRef<string | null>(null);
  const invalidatedRef = React.useRef<string | null>(null);

  if (conversationId !== activeConversationId) {
    setActiveConversationId(conversationId);
    setCommittedStreamKey(null);
    setDraftMessages([]);
    setProviderOverride(null);
  }

  const detailQuery = useQuery({
    queryKey: queryKeys.conversations.detail(conversationId ?? ""),
    queryFn: () => getConversation(conversationId!),
    enabled: Boolean(conversationId),
  });

  React.useEffect(() => {
    navigatedRef.current = null;
    invalidatedRef.current = null;
    stream.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional route switch
  }, [conversationId]);

  const serverMessages =
    conversationId && detailQuery.data?.id === conversationId ? detailQuery.data.messages : [];

  const provider = providerOverride ?? asProvider(detailQuery.data?.provider) ?? "gemini";

  const completedAssistant: ChatMessageView | null =
    stream.status === "completed" && stream.conversationId && stream.tokens
      ? {
          id: stream.messageId ?? `assistant-${stream.conversationId}`,
          role: "assistant",
          content: stream.tokens,
          createdAt: new Date().toISOString(),
          provider: stream.provider,
        }
      : null;

  const commitKey = completedAssistant
    ? (stream.messageId ??
      `${stream.conversationId}:${stream.tokens.length}:${stream.provider ?? ""}`)
    : null;

  if (commitKey && commitKey !== committedStreamKey && completedAssistant) {
    setCommittedStreamKey(commitKey);
    setDraftMessages((prev) => {
      if (prev.some((message) => message.id === completedAssistant.id)) {
        return prev;
      }
      return [...prev, completedAssistant];
    });
  }

  React.useEffect(() => {
    if (!commitKey || invalidatedRef.current === commitKey) {
      return;
    }
    invalidatedRef.current = commitKey;
    void queryClient.invalidateQueries({
      queryKey: queryKeys.conversations.all(),
    });
  }, [commitKey, queryClient]);

  React.useEffect(() => {
    if (!stream.conversationId || conversationId) {
      return;
    }
    if (navigatedRef.current === stream.conversationId) {
      return;
    }
    navigatedRef.current = stream.conversationId;

    if (stream.status === "streaming" || stream.status === "sending") {
      window.history.replaceState(null, "", `/chat/${stream.conversationId}`);
      return;
    }
    if (stream.status === "completed") {
      router.replace(`/chat/${stream.conversationId}`);
    }
  }, [conversationId, router, stream.conversationId, stream.status]);

  const localMessages = React.useMemo(() => {
    const base =
      draftMessages.length > 0 ? draftMessages : serverMessages.length > 0 ? serverMessages : [];
    if (completedAssistant && !base.some((message) => message.id === completedAssistant.id)) {
      return [...base, completedAssistant];
    }
    return base;
  }, [completedAssistant, draftMessages, serverMessages]);

  async function sendMessage(message: string, selectedProvider: LlmProvider) {
    const userMessage: ChatMessageView = {
      id: newId("user"),
      role: "user",
      content: message,
      createdAt: new Date().toISOString(),
    };
    setDraftMessages((prev) => {
      const base = prev.length > 0 ? prev : serverMessages;
      return [...base, userMessage];
    });
    setPendingRetry(message);
    setProviderOverride(selectedProvider);

    await stream.start({
      message,
      conversationId: conversationId ?? stream.conversationId,
      organizationId,
      provider: selectedProvider,
    });
  }

  const loadError =
    detailQuery.isError && isApiClientError(detailQuery.error)
      ? detailQuery.error
      : detailQuery.isError
        ? {
            status: 0,
            code: "LOAD_FAILED",
            message: "Could not load this conversation.",
          }
        : null;

  const showThreadSkeleton =
    Boolean(conversationId) && detailQuery.isLoading && localMessages.length === 0;

  return (
    <div className="border-border bg-background flex h-[calc(100svh-7.5rem)] min-h-[32rem] overflow-hidden rounded-xl border">
      <ConversationSidebar className="hidden w-72 shrink-0 lg:flex" />

      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-[min(100%,20rem)] p-0">
          <SheetHeader className="sr-only">
            <SheetTitle>Conversations</SheetTitle>
          </SheetHeader>
          <ConversationSidebar className="border-0" onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="border-border flex items-center gap-2 border-b px-3 py-2 lg:hidden">
          <Button
            type="button"
            size="icon"
            variant="ghost"
            aria-label="Open conversations"
            onClick={() => setMobileOpen(true)}
          >
            <PanelLeft className="h-4 w-4" />
          </Button>
          <p className="truncate text-sm font-medium">{detailQuery.data?.title ?? "Chat"}</p>
        </div>

        <div className="min-h-0 flex-1">
          {showThreadSkeleton ? (
            <div className="mx-auto max-w-3xl space-y-4 px-4 py-6">
              <Skeleton className="h-20 w-3/4" />
              <Skeleton className="ml-auto h-16 w-1/2" />
              <Skeleton className="h-28 w-4/5" />
            </div>
          ) : loadError ? (
            <ErrorState
              message={loadError.message}
              requestId={"requestId" in loadError ? loadError.requestId : undefined}
              onRetry={() => detailQuery.refetch()}
            />
          ) : (
            <ChatThread
              messages={localMessages}
              streamingContent={
                stream.status === "sending" ||
                stream.status === "streaming" ||
                stream.status === "cancelled" ||
                (stream.status === "error" && stream.tokens)
                  ? stream.tokens
                  : ""
              }
              isStreaming={stream.status === "sending" || stream.status === "streaming"}
              streamProvider={stream.provider}
              error={stream.status === "error" ? stream.error : null}
              onRetry={
                pendingRetry
                  ? () => {
                      void sendMessage(pendingRetry, provider);
                    }
                  : undefined
              }
              onSuggestion={(prompt) => {
                void sendMessage(prompt, provider);
              }}
            />
          )}
        </div>

        <div className="border-border border-t p-3">
          <ChatComposer
            provider={provider}
            onProviderChange={setProviderOverride}
            isBusy={stream.isBusy}
            disabled={Boolean(loadError)}
            onStop={stream.stop}
            onSubmit={({ message, provider: nextProvider }) => {
              void sendMessage(message, nextProvider);
            }}
          />
        </div>
      </div>
    </div>
  );
}
