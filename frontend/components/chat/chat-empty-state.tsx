import { MessageSquare } from "lucide-react";

import { EmptyState } from "@/components/feedback/empty-state";

const SUGGESTIONS = [
  "How do I debug a CrashLoopBackOff pod?",
  "Draft a multi-stage Node.js Dockerfile",
  "Explain this CI failure and suggest a fix",
];

export function ChatEmptyState({ onSuggestion }: { onSuggestion?: (prompt: string) => void }) {
  return (
    <EmptyState
      icon={<MessageSquare />}
      title="Start a conversation"
      description="Ask about logs, Kubernetes, pipelines, Dockerfiles, and DevOps best practices."
      action={
        onSuggestion ? (
          <div className="flex max-w-lg flex-col gap-2">
            {SUGGESTIONS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => onSuggestion(prompt)}
                className="border-border bg-card hover:border-primary/40 hover:bg-primary/5 rounded-lg border px-3 py-2 text-left text-sm transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        ) : undefined
      }
    />
  );
}
