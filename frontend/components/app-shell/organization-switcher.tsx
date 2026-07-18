"use client";

import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Check, ChevronsUpDown, User } from "lucide-react";
import { toast } from "sonner";

import { OPEN_ORG_SWITCHER_EVENT } from "@/components/app-shell/nav-config";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { components } from "@/lib/api/generated-types";
import { queryKeys } from "@/lib/api/query-keys";
import { cn } from "@/lib/utils/cn";
import { useWorkspaceStore } from "@/store/workspace-store";

type OrganizationResponse = components["schemas"]["OrganizationResponse"];
type OrganizationsPage = components["schemas"]["Page_OrganizationResponse_"];

function clearOrganizationScopedQueries(
  queryClient: ReturnType<typeof useQueryClient>,
  organizationId: string | null,
) {
  if (!organizationId) {
    return;
  }

  queryClient.removeQueries({
    predicate: (query) =>
      query.queryKey.some((part) => {
        if (part === organizationId) {
          return true;
        }
        if (typeof part === "object" && part !== null) {
          const record = part as Record<string, unknown>;
          return (
            record.organizationId === organizationId || record.organization_id === organizationId
          );
        }
        return false;
      }),
  });
}

export function OrganizationSwitcher({ className }: { className?: string }) {
  const queryClient = useQueryClient();
  const currentOrganizationId = useWorkspaceStore((s) => s.currentOrganizationId);
  const setOrganization = useWorkspaceStore((s) => s.setOrganization);
  const [open, setOpen] = React.useState(false);
  const triggerRef = React.useRef<HTMLButtonElement>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.organizations.list(),
    queryFn: () => apiFetch<OrganizationsPage>(endpoints.organizations.list()),
  });

  const organizations = data?.items ?? [];

  React.useEffect(() => {
    const onOpen = () => {
      setOpen(true);
      requestAnimationFrame(() => triggerRef.current?.focus());
    };
    window.addEventListener(OPEN_ORG_SWITCHER_EVENT, onOpen);
    return () => window.removeEventListener(OPEN_ORG_SWITCHER_EVENT, onOpen);
  }, []);

  const selected = organizations.find((org) => org.id === currentOrganizationId) ?? null;

  const switchTo = (organization: OrganizationResponse | null) => {
    const previousId = currentOrganizationId;
    const nextId = organization?.id ?? null;
    if (previousId === nextId) {
      setOpen(false);
      return;
    }

    setOrganization(nextId);
    clearOrganizationScopedQueries(queryClient, previousId);
    toast.success(
      organization ? `Switched to ${organization.name}` : "Switched to personal workspace",
    );
    setOpen(false);
  };

  const label = selected?.name ?? "Personal workspace";

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          ref={triggerRef}
          variant="outline"
          size="sm"
          className={cn("max-w-[220px] justify-between gap-2", className)}
          aria-label="Switch organization"
        >
          {selected ? (
            <Building2 className="h-4 w-4 shrink-0" aria-hidden />
          ) : (
            <User className="h-4 w-4 shrink-0" aria-hidden />
          )}
          <span className="truncate">{isLoading ? "Loading…" : label}</span>
          <ChevronsUpDown className="text-muted-foreground h-3.5 w-3.5 shrink-0" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        <DropdownMenuLabel>Workspace</DropdownMenuLabel>
        <DropdownMenuItem onSelect={() => switchTo(null)}>
          <User className="h-4 w-4" />
          <span className="flex-1 truncate">Personal workspace</span>
          {!currentOrganizationId ? <Check className="text-primary h-4 w-4" /> : null}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuLabel>Organizations</DropdownMenuLabel>
        {isError ? (
          <DropdownMenuItem disabled>Failed to load organizations</DropdownMenuItem>
        ) : null}
        {!isLoading && !isError && organizations.length === 0 ? (
          <DropdownMenuItem disabled>No organizations yet</DropdownMenuItem>
        ) : null}
        {organizations.map((org) => (
          <DropdownMenuItem key={org.id} onSelect={() => switchTo(org)}>
            <Building2 className="h-4 w-4" />
            <span className="flex min-w-0 flex-1 flex-col">
              <span className="truncate">{org.name}</span>
              <span className="text-muted-foreground truncate text-xs">{org.slug}</span>
            </span>
            {currentOrganizationId === org.id ? (
              <Check className="text-primary h-4 w-4 shrink-0" />
            ) : null}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
