"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Search } from "lucide-react";

import { breadcrumbSegments } from "@/components/app-shell/nav-config";
import { OrganizationSwitcher } from "@/components/app-shell/organization-switcher";
import { TaskStatusIndicator } from "@/components/app-shell/task-status-indicator";
import { ThemeToggle } from "@/components/app-shell/theme-toggle";
import { UserMenu } from "@/components/app-shell/user-menu";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { useUiStore } from "@/store/ui-store";

export function AppHeader() {
  const pathname = usePathname();
  const setSidebarMobileOpen = useUiStore((s) => s.setSidebarMobileOpen);
  const setCommandMenuOpen = useUiStore((s) => s.setCommandMenuOpen);
  const segments = breadcrumbSegments(pathname);

  return (
    <header className="bg-background/95 supports-[backdrop-filter]:bg-background/80 sticky top-0 z-30 flex h-14 items-center gap-3 border-b px-3 backdrop-blur md:px-4">
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        aria-label="Open navigation"
        onClick={() => setSidebarMobileOpen(true)}
      >
        <Menu className="h-4 w-4" />
      </Button>

      <Button
        variant="ghost"
        size="icon"
        className="hidden md:inline-flex"
        aria-label="Toggle sidebar"
        onClick={() => useUiStore.getState().toggleSidebarCollapsed()}
      >
        <Menu className="h-4 w-4" />
      </Button>

      <Breadcrumb className="min-w-0 flex-1">
        <BreadcrumbList>
          {segments.map((segment, index) => {
            const isLast = index === segments.length - 1;
            return (
              <div key={segment.href} className="contents">
                {index > 0 ? <BreadcrumbSeparator /> : null}
                <BreadcrumbItem>
                  {isLast ? (
                    <BreadcrumbPage className="truncate">{segment.label}</BreadcrumbPage>
                  ) : (
                    <BreadcrumbLink asChild>
                      <Link href={segment.href} className="truncate">
                        {segment.label}
                      </Link>
                    </BreadcrumbLink>
                  )}
                </BreadcrumbItem>
              </div>
            );
          })}
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex shrink-0 items-center gap-1 sm:gap-2">
        <OrganizationSwitcher className="hidden sm:inline-flex" />

        <Button
          variant="outline"
          size="sm"
          className="text-muted-foreground hidden gap-2 lg:inline-flex"
          onClick={() => setCommandMenuOpen(true)}
        >
          <Search className="h-3.5 w-3.5" />
          <span>Search</span>
          <kbd className="bg-muted pointer-events-none rounded border px-1.5 py-0.5 font-mono text-[10px]">
            ⌘K
          </kbd>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          aria-label="Open command menu"
          onClick={() => setCommandMenuOpen(true)}
        >
          <Search className="h-4 w-4" />
        </Button>

        <TaskStatusIndicator />
        <ThemeToggle />
        <UserMenu />
      </div>
    </header>
  );
}
