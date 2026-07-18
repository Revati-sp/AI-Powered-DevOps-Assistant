"use client";

import { ChevronsLeft, ChevronsRight } from "lucide-react";

import { SidebarNav } from "@/components/app-shell/sidebar-nav";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { APP_NAME } from "@/lib/constants/app";
import { cn } from "@/lib/utils/cn";
import { useUiStore } from "@/store/ui-store";

export function AppSidebar() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const toggleSidebarCollapsed = useUiStore((s) => s.toggleSidebarCollapsed);
  const collapseLabel = collapsed ? "Expand sidebar" : "Collapse sidebar";

  return (
    <aside
      className={cn(
        "bg-sidebar text-sidebar-foreground border-sidebar-border sticky top-0 hidden h-svh shrink-0 flex-col border-r transition-[width] duration-200 md:flex",
        collapsed ? "w-16" : "w-64",
      )}
      aria-label="Application sidebar"
    >
      <div className={cn("flex h-14 items-center gap-2 px-3", collapsed && "justify-center px-2")}>
        <div className="bg-sidebar-primary text-sidebar-primary-foreground flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-xs font-bold">
          AD
        </div>
        {!collapsed ? (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-tight">{APP_NAME}</p>
            <p className="text-muted-foreground truncate text-xs">Workspace</p>
          </div>
        ) : null}
      </div>
      <Separator className="bg-sidebar-border" />
      <ScrollArea className="flex-1 px-2 py-4">
        <SidebarNav collapsed={collapsed} />
      </ScrollArea>
      <Separator className="bg-sidebar-border" />
      <div className={cn("p-2", collapsed && "flex justify-center")}>
        <TooltipProvider delayDuration={0}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size={collapsed ? "icon" : "sm"}
                aria-label={collapseLabel}
                aria-expanded={!collapsed}
                onClick={toggleSidebarCollapsed}
                className={cn("text-sidebar-foreground", !collapsed && "w-full justify-start")}
              >
                {collapsed ? (
                  <ChevronsRight className="h-4 w-4" />
                ) : (
                  <>
                    <ChevronsLeft className="h-4 w-4" />
                    Collapse
                  </>
                )}
              </Button>
            </TooltipTrigger>
            {collapsed ? <TooltipContent side="right">{collapseLabel}</TooltipContent> : null}
          </Tooltip>
        </TooltipProvider>
      </div>
    </aside>
  );
}
