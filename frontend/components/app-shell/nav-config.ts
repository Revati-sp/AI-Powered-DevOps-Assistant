import type { LucideIcon } from "lucide-react";
import {
  Boxes,
  Building2,
  Container,
  FileCode2,
  FileSearch,
  GitBranch,
  LayoutDashboard,
  ListTodo,
  MessageSquare,
  Package,
  ScrollText,
  Settings,
  Shield,
  Terminal,
} from "lucide-react";

import type { OrgRole, Permission } from "@/lib/permissions/rbac";
import { can } from "@/lib/permissions/rbac";

export const OPEN_ORG_SWITCHER_EVENT = "ada:open-org-switcher";

export type NavContext = {
  organizationId: string | null;
  orgRole: OrgRole | null;
};

export type NavItemConfig = {
  id: string;
  title: string;
  icon: LucideIcon;
  /** Static href, or resolve from workspace context. Return null to hide. */
  href: string | ((ctx: NavContext) => string | null);
  permission?: Permission;
  /** Hide when no organization is selected. */
  requiresOrganization?: boolean;
};

export type NavGroupConfig = {
  id: string;
  title: string;
  items: NavItemConfig[];
};

export const NAV_GROUPS: NavGroupConfig[] = [
  {
    id: "overview",
    title: "Overview",
    items: [
      {
        id: "dashboard",
        title: "Dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
      },
    ],
  },
  {
    id: "ai-operations",
    title: "AI Operations",
    items: [
      { id: "chat", title: "Chat", href: "/chat", icon: MessageSquare },
      { id: "logs", title: "Log Analyzer", href: "/logs", icon: FileSearch },
      {
        id: "reviews",
        title: "Configuration Review",
        href: "/reviews",
        icon: FileCode2,
      },
    ],
  },
  {
    id: "generators",
    title: "Generators",
    items: [
      {
        id: "dockerfile",
        title: "Dockerfile",
        href: "/generators/dockerfile",
        icon: Container,
      },
      {
        id: "kubernetes",
        title: "Kubernetes",
        href: "/generators/kubernetes",
        icon: Boxes,
      },
      {
        id: "pipeline",
        title: "CI/CD Pipeline",
        href: "/generators/pipeline",
        icon: GitBranch,
      },
      {
        id: "command",
        title: "Shell Command",
        href: "/generators/command",
        icon: Terminal,
      },
    ],
  },
  {
    id: "workspace",
    title: "Workspace",
    items: [
      { id: "artifacts", title: "Artifacts", href: "/artifacts", icon: Package },
      {
        id: "organizations",
        title: "Organizations",
        href: "/organizations",
        icon: Building2,
      },
      { id: "tasks", title: "Tasks", href: "/tasks", icon: ListTodo },
    ],
  },
  {
    id: "administration",
    title: "Administration",
    items: [
      {
        id: "policy-packs",
        title: "Policy Packs",
        icon: Shield,
        href: (ctx) =>
          ctx.organizationId ? `/organizations/${ctx.organizationId}/policies` : "/organizations",
      },
      {
        id: "audit-logs",
        title: "Audit Logs",
        icon: ScrollText,
        requiresOrganization: true,
        permission: "audit.read",
        href: (ctx) => (ctx.organizationId ? `/organizations/${ctx.organizationId}/audit` : null),
      },
    ],
  },
  {
    id: "account",
    title: "Account",
    items: [
      {
        id: "settings",
        title: "Settings",
        href: "/settings/profile",
        icon: Settings,
      },
    ],
  },
];

export type ResolvedNavItem = {
  id: string;
  title: string;
  href: string;
  icon: LucideIcon;
  permission?: Permission;
};

export type ResolvedNavGroup = {
  id: string;
  title: string;
  items: ResolvedNavItem[];
};

export function resolveNavGroups(ctx: NavContext): ResolvedNavGroup[] {
  return NAV_GROUPS.map((group) => {
    const items = group.items
      .map((item): ResolvedNavItem | null => {
        if (item.requiresOrganization && !ctx.organizationId) {
          return null;
        }
        if (item.permission) {
          if (!ctx.orgRole || !can(ctx.orgRole, item.permission)) {
            return null;
          }
        }
        const href = typeof item.href === "function" ? item.href(ctx) : item.href;
        if (!href) {
          return null;
        }
        return {
          id: item.id,
          title: item.title,
          href,
          icon: item.icon,
          permission: item.permission,
        };
      })
      .filter((item): item is ResolvedNavItem => item !== null);

    return { id: group.id, title: group.title, items };
  }).filter((group) => group.items.length > 0);
}

export function isNavItemActive(pathname: string, href: string): boolean {
  if (pathname === href) {
    return true;
  }
  if (href === "/dashboard") {
    return false;
  }
  return pathname.startsWith(`${href}/`);
}

const SEGMENT_LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  chat: "Chat",
  logs: "Log Analyzer",
  reviews: "Configuration Review",
  generators: "Generators",
  dockerfile: "Dockerfile",
  kubernetes: "Kubernetes",
  pipeline: "CI/CD Pipeline",
  command: "Shell Command",
  artifacts: "Artifacts",
  organizations: "Organizations",
  members: "Members",
  policies: "Policy Packs",
  audit: "Audit Logs",
  tasks: "Tasks",
  settings: "Settings",
  profile: "Profile",
  appearance: "Appearance",
  security: "Security",
};

export function breadcrumbSegments(pathname: string): { label: string; href: string }[] {
  const parts = pathname.split("/").filter(Boolean);
  const segments: { label: string; href: string }[] = [];
  let href = "";

  for (const part of parts) {
    href += `/${part}`;
    const label =
      SEGMENT_LABELS[part] ??
      (part.length > 20 ? `${part.slice(0, 8)}…` : decodeURIComponent(part));
    segments.push({ label, href });
  }

  return segments;
}

export function humanizeSegment(segment: string): string {
  return (
    SEGMENT_LABELS[segment] ??
    segment.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

export const COMMAND_ACTIONS = [
  {
    id: "new-chat",
    label: "New chat",
    href: "/chat",
    keywords: ["conversation", "ai"],
  },
  {
    id: "analyze-logs",
    label: "Analyze logs",
    href: "/logs",
    keywords: ["log", "analyzer"],
  },
  {
    id: "generate-dockerfile",
    label: "Generate Dockerfile",
    href: "/generators/dockerfile",
    keywords: ["docker", "container"],
  },
  {
    id: "generate-kubernetes",
    label: "Generate Kubernetes",
    href: "/generators/kubernetes",
    keywords: ["k8s", "manifest"],
  },
  {
    id: "review-config",
    label: "Review config",
    href: "/reviews",
    keywords: ["configuration", "review"],
  },
  {
    id: "artifacts",
    label: "Artifacts",
    href: "/artifacts",
    keywords: ["files", "versions"],
  },
  {
    id: "switch-org",
    label: "Switch organization",
    href: null,
    keywords: ["workspace", "org", "organization"],
  },
  {
    id: "settings",
    label: "Settings",
    href: "/settings/profile",
    keywords: ["account", "profile"],
  },
] as const;
