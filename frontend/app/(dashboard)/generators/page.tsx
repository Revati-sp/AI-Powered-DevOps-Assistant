import type { Metadata } from "next";
import Link from "next/link";
import { Boxes, Container, GitBranch, Terminal, WandSparkles } from "lucide-react";

import { PageHeader } from "@/components/data-display/page-header";
import { EmptyState } from "@/components/feedback/empty-state";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Generators",
};

const GENERATORS = [
  {
    href: "/generators/dockerfile",
    title: "Dockerfile",
    description: "Generate optimized container build files.",
    icon: Container,
  },
  {
    href: "/generators/kubernetes",
    title: "Kubernetes",
    description: "Produce manifests for common workloads.",
    icon: Boxes,
  },
  {
    href: "/generators/pipeline",
    title: "CI/CD Pipeline",
    description: "Scaffold GitHub Actions or similar pipelines.",
    icon: GitBranch,
  },
  {
    href: "/generators/command",
    title: "Shell Command",
    description: "Draft safe, explainable shell commands.",
    icon: Terminal,
  },
] as const;

export default function GeneratorsIndexPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Generators"
        description="Create infrastructure and automation artifacts with guided AI generation."
      />
      <div className="grid gap-3 sm:grid-cols-2">
        {GENERATORS.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="hover:border-primary/40 hover:bg-muted/40 focus-visible:ring-ring rounded-lg border p-4 transition-colors focus-visible:ring-2 focus-visible:outline-none"
            >
              <div className="flex items-start gap-3">
                <Icon className="text-primary mt-0.5 h-5 w-5 shrink-0" />
                <div className="space-y-1">
                  <p className="text-sm font-semibold">{item.title}</p>
                  <p className="text-muted-foreground text-sm">{item.description}</p>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
      <EmptyState
        icon={<WandSparkles />}
        title="Pick a generator to begin"
        description="Each generator walks through inputs and returns an editable artifact you can save."
        action={
          <Button asChild variant="outline" size="sm">
            <Link href="/generators/dockerfile">Start with Dockerfile</Link>
          </Button>
        }
      />
    </div>
  );
}
