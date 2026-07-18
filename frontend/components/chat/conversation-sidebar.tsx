"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { isToday, isYesterday, parseISO, startOfDay, subDays } from "date-fns";
import { MessageSquarePlus, Search, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { ProviderBadge } from "@/components/chat/provider-badge";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";
import { EmptyState } from "@/components/feedback/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { deleteConversation, listConversations } from "@/features/chat/api";
import type { ConversationDateGroup, ConversationListItem } from "@/features/chat/types";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { isApiClientError } from "@/lib/api/errors";
import { queryKeys } from "@/lib/api/query-keys";
import { formatRelative } from "@/lib/formatters/date";
import { cn } from "@/lib/utils/cn";
import { useWorkspaceStore } from "@/store/workspace-store";

function groupConversations(items: ConversationListItem[]): ConversationDateGroup[] {
  const groups: ConversationDateGroup[] = [];
  const buckets = new Map<string, ConversationListItem[]>();

  const sorted = [...items].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
  );

  for (const item of sorted) {
    const date = parseISO(item.updatedAt);
    let label = "Older";
    if (isToday(date)) {
      label = "Today";
    } else if (isYesterday(date)) {
      label = "Yesterday";
    } else if (date >= startOfDay(subDays(new Date(), 7))) {
      label = "Previous 7 days";
    }

    const list = buckets.get(label) ?? [];
    list.push(item);
    buckets.set(label, list);
  }

  for (const label of ["Today", "Yesterday", "Previous 7 days", "Older"]) {
    const conversations = buckets.get(label);
    if (conversations?.length) {
      groups.push({ label, conversations });
    }
  }

  return groups;
}

export function ConversationSidebar({
  className,
  onNavigate,
}: {
  className?: string;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [search, setSearch] = React.useState("");
  const [provider, setProvider] = React.useState<string>("all");
  const [offset, setOffset] = React.useState(0);
  const [pendingDeleteId, setPendingDeleteId] = React.useState<string | null>(null);
  const organizationId = useWorkspaceStore((state) => state.currentOrganizationId);
  const debouncedSearch = useDebouncedValue(search);
  const filters = {
    limit: 30,
    offset,
    search: debouncedSearch || undefined,
    provider: provider === "all" ? undefined : provider,
    organization_id: organizationId,
    sort_by: "updated_at" as const,
    sort_order: "desc" as const,
  };

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: queryKeys.conversations.list(filters),
    queryFn: () => listConversations(filters),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteConversation,
    onSuccess: async (_data, conversationId) => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.conversations.all(),
      });
      toast.success("Conversation deleted");
      if (pathname === `/chat/${conversationId}`) {
        router.push("/chat");
      }
      setPendingDeleteId(null);
    },
    onError: (error) => {
      toast.error(isApiClientError(error) ? error.message : "Could not delete conversation");
    },
  });

  const groups = React.useMemo(() => groupConversations(data?.items ?? []), [data?.items]);

  return (
    <aside
      className={cn("border-border bg-card/40 flex h-full min-h-0 flex-col border-r", className)}
    >
      <div className="space-y-3 p-3">
        <Button asChild className="w-full">
          <Link href="/chat" onClick={onNavigate}>
            <MessageSquarePlus className="h-4 w-4" />
            New chat
          </Link>
        </Button>
        <div className="relative">
          <Search className="text-muted-foreground absolute top-2.5 left-2.5 h-4 w-4" />
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setOffset(0);
            }}
            placeholder="Search conversations"
            className="pl-8"
            aria-label="Search conversations"
          />
        </div>
        <Select value={provider} onValueChange={(value) => { setProvider(value); setOffset(0); }}>
          <SelectTrigger aria-label="Filter by provider"><SelectValue placeholder="All providers" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All providers</SelectItem>
            <SelectItem value="gemini">Gemini</SelectItem>
            <SelectItem value="llama">Llama</SelectItem>
            <SelectItem value="mistral">Mistral</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <ScrollArea className="min-h-0 flex-1 px-2 pb-3">
        {isLoading ? (
          <div className="space-y-2 p-2">
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} className="h-14 w-full" />
            ))}
          </div>
        ) : isError ? (
          <div className="p-3 text-center">
            <p className="text-muted-foreground mb-2 text-sm">
              {isApiClientError(error)
                ? `${error.message}${error.retryAfterSeconds !== undefined ? ` Try again in ${error.retryAfterSeconds}s.` : ""}${error.requestId ? ` (Request ID: ${error.requestId})` : ""}`
                : "Could not load conversations."}
            </p>
            <Button size="sm" variant="outline" onClick={() => refetch()}>Retry</Button>
          </div>
        ) : groups.length === 0 ? (
          <EmptyState
            className="py-8"
            title="No conversations"
            description={
              search.trim()
                ? "No conversations match your search."
                : "Start a new chat to see it listed here."
            }
          />
        ) : (
          <div className="space-y-4">
            {groups.map((group) => (
              <div key={group.label} className="space-y-1">
                <p className="text-muted-foreground px-2 text-xs font-medium tracking-wide uppercase">
                  {group.label}
                </p>
                <ul className="space-y-1">
                  {group.conversations.map((item) => {
                    const href = `/chat/${item.id}`;
                    const active = pathname === href;
                    return (
                      <li key={item.id}>
                        <div
                          className={cn(
                            "group hover:bg-muted/60 flex items-start gap-1 rounded-lg px-2 py-2 transition-colors",
                            active && "bg-primary/10 hover:bg-primary/10",
                          )}
                        >
                          <Link
                            href={href}
                            onClick={onNavigate}
                            className="min-w-0 flex-1 space-y-1"
                          >
                            <p className="truncate text-sm font-medium">
                              {item.title || "Untitled chat"}
                            </p>
                            <div className="flex items-center gap-2">
                              <ProviderBadge provider={item.provider} />
                              <span className="text-muted-foreground text-[11px]">
                                {formatRelative(item.updatedAt)}
                              </span>
                            </div>
                          </Link>
                          <Button
                            type="button"
                            size="icon"
                            variant="ghost"
                            className="text-muted-foreground hover:text-destructive h-7 w-7 opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
                            aria-label={`Delete ${item.title || "conversation"}`}
                            onClick={() => setPendingDeleteId(item.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
            <div className="flex items-center justify-between px-2">
              <Button size="sm" variant="ghost" disabled={offset === 0 || isFetching} onClick={() => setOffset((value) => Math.max(0, value - 30))}>Previous</Button>
              <span className="text-muted-foreground text-xs">{offset + 1}–{Math.min(offset + 30, data?.total ?? 0)} of {data?.total ?? 0}</span>
              <Button size="sm" variant="ghost" disabled={!data || offset + data.limit >= data.total || isFetching} onClick={() => setOffset((value) => value + 30)}>Next</Button>
            </div>
          </div>
        )}
      </ScrollArea>

      <ConfirmationDialog
        open={pendingDeleteId !== null}
        onOpenChange={(open) => {
          if (!open) {
            setPendingDeleteId(null);
          }
        }}
        title="Delete conversation?"
        description="This permanently removes the conversation and its messages."
        confirmLabel="Delete"
        variant="destructive"
        loading={deleteMutation.isPending}
        onConfirm={() => {
          if (pendingDeleteId) {
            deleteMutation.mutate(pendingDeleteId);
          }
        }}
      />
    </aside>
  );
}
