import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { components } from "@/lib/api/generated-types";
import { buildQueryString } from "@/lib/api/query-string";

import type {
  ChatMessageRole,
  ChatMessageView,
  ConversationDetailView,
  ConversationListFilters,
  ConversationListItem,
  ConversationsPage,
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
    organizationId: item.organization_id,
  };
}

export async function listConversations(
  filters: ConversationListFilters = {},
): Promise<ConversationsPage> {
  const query = buildQueryString({
    limit: filters.limit ?? 30,
    offset: filters.offset ?? 0,
    search: filters.search?.trim() || undefined,
    provider: filters.provider || undefined,
    organization_id: filters.organization_id ?? undefined,
    created_from: filters.created_from,
    created_to: filters.created_to,
    sort_by: filters.sort_by ?? "updated_at",
    sort_order: filters.sort_order ?? "desc",
  });
  const data = await apiFetch<{
    items: ConversationSummary[];
    total: number;
    limit: number;
    offset: number;
  }>(`${endpoints.chat.conversations()}${query}`);

  return {
    items: (data.items ?? []).map(mapSummary),
    total: data.total,
    limit: data.limit,
    offset: data.offset,
  };
}

export async function getConversation(conversationId: string): Promise<ConversationDetailView> {
  const data = await apiFetch<ConversationDetail>(endpoints.chat.conversation(conversationId));
  return {
    id: data.id,
    title: data.title,
    provider: data.provider,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    organizationId: data.organization_id,
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
