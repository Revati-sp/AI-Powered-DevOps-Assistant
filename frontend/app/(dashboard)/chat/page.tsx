import { ChatWorkspace } from "@/components/chat/chat-workspace";
import { PageHeader } from "@/components/data-display/page-header";

export default function ChatPage() {
  return (
    <div className="space-y-4">
      <PageHeader
        title="Chat"
        description="Ask the DevOps assistant about infrastructure, incidents, and best practices."
      />
      <ChatWorkspace />
    </div>
  );
}
