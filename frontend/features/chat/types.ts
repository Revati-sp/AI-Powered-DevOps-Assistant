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
};

export type ConversationDetailView = {
  id: string;
  title: string;
  provider: string;
  createdAt: string;
  updatedAt: string;
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
