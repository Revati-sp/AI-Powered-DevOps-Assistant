import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { components } from "@/lib/api/generated-types";

import type {
  ChatMessageRole,
  ChatMessageView,
  ConversationDetailView,
  ConversationListItem,
} from "@/features/chat/types";

type ConversationSummary = components["schemas"]["ConversationSummary"];
type ConversationDetail = components["schemas"]["ConversationDetail"];
type MessageResponse = components["schemas"]["MessageResponse"];
type ChatRequest = components["schemas"]["ChatRequest"];
type ChatResponse = components["schemas"]["ChatResponse"];

function mapMessage(message: MessageResponse): ChatMessageView {
  const role = (["user", "assistant", "system"] as const).includes(message.role as ChatMessageRole)
    ? (message.role as ChatMessageRole)
    : "assistant";

  return {
    id: message.id,
    role,
    content: message.content,
    createdAt: message.created_at,
  };
}

function mapSummary(item: ConversationSummary): ConversationListItem {
  return {
    id: item.id,
    title: item.title,
    provider: item.provider,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  };
}

export async function listConversations(): Promise<ConversationListItem[]> {
  const data = await apiFetch<ConversationSummary[]>(endpoints.chat.conversations());
  return (data ?? []).map(mapSummary);
}

export async function getConversation(conversationId: string): Promise<ConversationDetailView> {
  const data = await apiFetch<ConversationDetail>(endpoints.chat.conversation(conversationId));
  return {
    id: data.id,
    title: data.title,
    provider: data.provider,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    messages: (data.messages ?? []).map(mapMessage),
  };
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await apiFetch<null>(endpoints.chat.deleteConversation(conversationId), {
    method: "DELETE",
  });
}

export async function sendChat(request: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  return apiFetch<ChatResponse>(endpoints.chat.chat(), {
    method: "POST",
    body: request,
    signal,
  });
}
