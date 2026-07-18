"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  isNavItemActive,
  resolveNavGroups,
  type ResolvedNavItem,
} from "@/components/app-shell/nav-config";
import { useOrgRole } from "@/components/app-shell/use-org-role";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils/cn";
import { useWorkspaceStore } from "@/store/workspace-store";

type SidebarNavProps = {
  collapsed?: boolean;
  onNavigate?: () => void;
  className?: string;
};

type IndexedNavItem = {
  item: ResolvedNavItem;
  index: number;
};

export function SidebarNav({ collapsed = false, onNavigate, className }: SidebarNavProps) {
  const pathname = usePathname();
  const organizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const orgRole = useOrgRole();

  const groups = React.useMemo(
    () => resolveNavGroups({ organizationId, orgRole }),
    [organizationId, orgRole],
  );

  const flatItems = React.useMemo(() => groups.flatMap((group) => group.items), [groups]);

  const indexedGroups = React.useMemo(() => {
    const offsets = groups.reduce<number[]>((acc, group, groupIndex) => {
      const previous =
        groupIndex === 0 ? 0 : acc[groupIndex - 1] + groups[groupIndex - 1].items.length;
      acc.push(previous);
      return acc;
    }, []);

    return groups.map((group, groupIndex) => ({
      ...group,
      items: group.items.map((item, itemIndex): IndexedNavItem => ({
        item,
        index: offsets[groupIndex] + itemIndex,
      })),
    }));
  }, [groups]);

  const activeIndex = React.useMemo(() => {
    const index = flatItems.findIndex((item) => isNavItemActive(pathname, item.href));
    return index >= 0 ? index : 0;
  }, [flatItems, pathname]);

  const [rovingIndex, setRovingIndex] = React.useState<number | null>(null);
  const focusIndex = rovingIndex ?? activeIndex;
  const itemRefs = React.useRef<Array<HTMLAnchorElement | null>>([]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLAnchorElement>, index: number) => {
    if (flatItems.length === 0) {
      return;
    }

    let next = index;
    if (event.key === "ArrowDown" || event.key === "ArrowRight") {
      event.preventDefault();
      next = (index + 1) % flatItems.length;
    } else if (event.key === "ArrowUp" || event.key === "ArrowLeft") {
      event.preventDefault();
      next = (index - 1 + flatItems.length) % flatItems.length;
    } else if (event.key === "Home") {
      event.preventDefault();
      next = 0;
    } else if (event.key === "End") {
      event.preventDefault();
      next = flatItems.length - 1;
    } else {
      return;
    }

    setRovingIndex(next);
    itemRefs.current[next]?.focus();
  };

  return (
    <TooltipProvider delayDuration={0}>
      <nav aria-label="Main" className={cn("flex flex-col gap-6", className)}>
        {indexedGroups.map((group) => (
          <div key={group.id} className="space-y-1">
            {!collapsed ? (
              <p className="text-muted-foreground px-3 text-xs font-semibold tracking-wide uppercase">
                {group.title}
              </p>
            ) : (
              <span className="sr-only">{group.title}</span>
            )}
            <ul className="space-y-0.5" role="list">
              {group.items.map(({ item, index }) => (
                <li key={item.id}>
                  <NavLink
                    item={item}
                    collapsed={collapsed}
                    active={isNavItemActive(pathname, item.href)}
                    tabIndex={focusIndex === index ? 0 : -1}
                    ref={(el) => {
                      itemRefs.current[index] = el;
                    }}
                    onKeyDown={(event) => handleKeyDown(event, index)}
                    onClick={onNavigate}
                  />
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
    </TooltipProvider>
  );
}

const NavLink = React.forwardRef<
  HTMLAnchorElement,
  {
    item: ResolvedNavItem;
    collapsed: boolean;
    active: boolean;
    tabIndex: number;
    onKeyDown: (event: React.KeyboardEvent<HTMLAnchorElement>) => void;
    onClick?: () => void;
  }
>(function NavLink({ item, collapsed, active, tabIndex, onKeyDown, onClick }, ref) {
  const Icon = item.icon;
  const link = (
    <Link
      ref={ref}
      href={item.href}
      tabIndex={tabIndex}
      onKeyDown={onKeyDown}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      className={cn(
        "focus-visible:ring-sidebar-ring flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:outline-none",
        collapsed && "justify-center px-2",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
      )}
    >
      <Icon className="h-4 w-4 shrink-0" aria-hidden />
      {!collapsed ? <span className="truncate">{item.title}</span> : null}
      {collapsed ? <span className="sr-only">{item.title}</span> : null}
    </Link>
  );

  if (!collapsed) {
    return link;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{link}</TooltipTrigger>
      <TooltipContent side="right">{item.title}</TooltipContent>
    </Tooltip>
  );
});
