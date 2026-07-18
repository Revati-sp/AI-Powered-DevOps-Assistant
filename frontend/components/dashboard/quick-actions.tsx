import Link from "next/link";
import { FileCode2, MessageSquare, ScrollText, Sparkles } from "lucide-react";

import { SectionHeader } from "@/components/data-display/section-header";
import { Card, CardContent } from "@/components/ui/card";

const ACTIONS = [
  {
    href: "/chat",
    title: "New chat",
    description: "Ask the assistant about an incident or config",
    icon: MessageSquare,
  },
  {
    href: "/generators",
    title: "Generate",
    description: "Create Dockerfiles, K8s manifests, or pipelines",
    icon: Sparkles,
  },
  {
    href: "/logs",
    title: "Analyze logs",
    description: "Paste or upload logs for triage help",
    icon: ScrollText,
  },
  {
    href: "/artifacts",
    title: "Browse artifacts",
    description: "Open recently generated workspace assets",
    icon: FileCode2,
  },
] as const;

export function QuickActions() {
  return (
    <Card>
      <CardContent className="space-y-4 p-6">
        <SectionHeader title="Quick actions" description="Jump into the most common workflows" />
        <div className="grid gap-3 sm:grid-cols-2">
          {ACTIONS.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className="border-border hover:border-primary/40 hover:bg-primary/5 group rounded-xl border p-4 transition-colors"
            >
              <div className="mb-2 flex items-center gap-2">
                <action.icon className="text-primary h-4 w-4" />
                <p className="text-sm font-medium">{action.title}</p>
              </div>
              <p className="text-muted-foreground text-xs">{action.description}</p>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
