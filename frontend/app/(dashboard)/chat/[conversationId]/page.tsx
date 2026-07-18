import { ChatWorkspace } from "@/components/chat/chat-workspace";
import { PageHeader } from "@/components/data-display/page-header";

type ChatConversationPageProps = {
  params: Promise<{ conversationId: string }>;
};

export default async function ChatConversationPage({ params }: ChatConversationPageProps) {
  const { conversationId } = await params;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Conversation"
        description="Continue your chat with the DevOps assistant."
      />
      <ChatWorkspace conversationId={conversationId} />
    </div>
  );
}
