"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { COMMAND_ACTIONS, OPEN_ORG_SWITCHER_EVENT } from "@/components/app-shell/nav-config";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { useUiStore } from "@/store/ui-store";

export function CommandMenu() {
  const router = useRouter();
  const open = useUiStore((s) => s.commandMenuOpen);
  const setCommandMenuOpen = useUiStore((s) => s.setCommandMenuOpen);

  React.useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.key === "k" || event.key === "K") && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        setCommandMenuOpen(!useUiStore.getState().commandMenuOpen);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [setCommandMenuOpen]);

  const runAction = (actionId: string, href: string | null) => {
    setCommandMenuOpen(false);
    if (actionId === "switch-org") {
      window.dispatchEvent(new Event(OPEN_ORG_SWITCHER_EVENT));
      return;
    }
    if (href) {
      router.push(href);
    }
  };

  return (
    <CommandDialog open={open} onOpenChange={setCommandMenuOpen}>
      <CommandInput placeholder="Search commands…" />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Actions">
          {COMMAND_ACTIONS.map((action) => (
            <CommandItem
              key={action.id}
              value={`${action.label} ${action.keywords.join(" ")}`}
              onSelect={() => runAction(action.id, action.href)}
            >
              {action.label}
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
