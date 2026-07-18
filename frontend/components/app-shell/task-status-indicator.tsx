"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Loader2, ListTodo } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { components } from "@/lib/api/generated-types";
import { queryKeys } from "@/lib/api/query-keys";

type TasksPage = components["schemas"]["Page_TaskSummaryResponse_"];

export function TaskStatusIndicator() {
  const { data } = useQuery({
    queryKey: queryKeys.tasks.list({ active: true }),
    queryFn: () => apiFetch<TasksPage>(`${endpoints.tasks.list()}?limit=20&offset=0`),
    refetchInterval: 15_000,
  });

  const activeCount =
    data?.items.filter((task) => task.status === "queued" || task.status === "running").length ?? 0;

  return (
    <TooltipProvider delayDuration={0}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            asChild
            variant="ghost"
            size="icon"
            className="relative"
            aria-label={activeCount > 0 ? `${activeCount} active tasks` : "View tasks"}
          >
            <Link href="/tasks">
              {activeCount > 0 ? (
                <Loader2 className="text-primary h-4 w-4 animate-spin" />
              ) : (
                <ListTodo className="h-4 w-4" />
              )}
              {activeCount > 0 ? (
                <span className="bg-primary text-primary-foreground absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full px-1 text-[10px] font-semibold">
                  {activeCount > 9 ? "9+" : activeCount}
                </span>
              ) : null}
            </Link>
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          {activeCount > 0 ? `${activeCount} active task${activeCount === 1 ? "" : "s"}` : "Tasks"}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
