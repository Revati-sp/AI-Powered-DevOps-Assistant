"use client";

import { SidebarNav } from "@/components/app-shell/sidebar-nav";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { APP_NAME } from "@/lib/constants/app";
import { useUiStore } from "@/store/ui-store";

export function MobileNavigation() {
  const open = useUiStore((s) => s.sidebarMobileOpen);
  const setSidebarMobileOpen = useUiStore((s) => s.setSidebarMobileOpen);

  return (
    <Sheet open={open} onOpenChange={setSidebarMobileOpen}>
      <SheetContent side="left" className="bg-sidebar w-72 p-0 sm:max-w-xs">
        <SheetHeader className="border-sidebar-border border-b px-4 py-4 text-left">
          <SheetTitle className="text-sidebar-foreground text-base">{APP_NAME}</SheetTitle>
          <SheetDescription>Navigate the workspace</SheetDescription>
        </SheetHeader>
        <div className="px-2 py-4">
          <SidebarNav onNavigate={() => setSidebarMobileOpen(false)} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
