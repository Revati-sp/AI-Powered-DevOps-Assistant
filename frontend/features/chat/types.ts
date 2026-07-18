import type { LlmProvider } from "@/lib/constants/app";

export type ChatMessageRole = "user" | "assistant" | "system";

export type ChatMessageView = {
  id: string;
  role: ChatMessageRole;
  content: string;
  createdAt: string;
  provider?: string | null;
  isStreaming?: boolean;
};

export type ConversationListItem = {
  id: string;
  title: string;
  provider: string;
  createdAt: string;
  updatedAt: string;
  organizationId?: string | null;
};

export type ConversationsPage = {
  items: ConversationListItem[];
  total: number;
  limit: number;
  offset: number;
};

export type ConversationListFilters = {
  limit?: number;
  offset?: number;
  search?: string;
  provider?: string;
  organization_id?: string | null;
  created_from?: string;
  created_to?: string;
  sort_by?: "created_at" | "updated_at" | "title";
  sort_order?: "asc" | "desc";
};

export type ConversationDetailView = ConversationListItem & {
  messages: ChatMessageView[];
};

export type ConversationDateGroup = {
  label: string;
  conversations: ConversationListItem[];
};

export type ChatComposerValues = {
  message: string;
  provider: LlmProvider;
};

export type StreamingChatStatus =
  "idle" | "sending" | "streaming" | "completed" | "cancelled" | "error";
