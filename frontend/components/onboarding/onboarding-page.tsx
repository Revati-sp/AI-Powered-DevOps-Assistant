"use client";

import { Check, Copy } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { OnboardingChecklist } from "@/components/onboarding/onboarding-checklist";
import { PageHeader } from "@/components/data-display/page-header";
import { SectionHeader } from "@/components/data-display/section-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { usePatchOnboarding } from "@/features/onboarding/hooks";
import { isApiClientError } from "@/lib/api/errors";

const SAMPLE_PROMPTS = [
  {
    title: "Chat — debug a failing deployment",
    target: "Paste into Chat",
    href: "/chat",
    prompt:
      "My Kubernetes deployment `api-server` is stuck in CrashLoopBackOff. What logs and kubectl commands should I run first to diagnose it?",
  },
  {
    title: "Log analyzer — parse CI output",
    target: "Paste into Log Analyzer",
    href: "/logs",
    prompt:
      "Analyze this CI log snippet and summarize the root cause, failed step, and suggested fix:\n\n[ paste log excerpt here ]",
  },
  {
    title: "Artifact — starter Dockerfile",
    target: "Paste into New artifact",
    href: "/artifacts",
    prompt:
      "FROM node:20-alpine\nWORKDIR /app\nCOPY package*.json ./\nRUN npm ci --omit=dev\nCOPY . .\nEXPOSE 3000\nCMD [\"npm\", \"start\"]",
  },
  {
    title: "Policy review — nginx config",
    target: "Paste into Configuration Review",
    href: "/reviews",
    prompt:
      "Review this nginx config for security and reliability issues:\n\nserver {\n  listen 80;\n  location / {\n    proxy_pass http://backend:8080;\n  }\n}",
  },
];

function CopyPromptButton({ text }: { text: string }) {
  const [copied, setCopied] = React.useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Could not copy to clipboard");
    }
  };

  return (
    <Button type="button" variant="outline" size="sm" onClick={() => void copy()}>
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      Copy prompt
    </Button>
  );
}

export function OnboardingPageClient() {
  const patchMutation = usePatchOnboarding();

  const completeTour = async () => {
    try {
      await patchMutation.mutateAsync({ tour_completed: true });
      toast.success("Tour marked complete");
    } catch (err) {
      toast.error(isApiClientError(err) ? err.message : "Failed to save progress");
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Getting started"
        description="Follow the checklist and try sample prompts to explore core DevOps workflows."
        actions={
          <Button
            type="button"
            variant="outline"
            disabled={patchMutation.isPending}
            onClick={() => void completeTour()}
          >
            Mark tour complete
          </Button>
        }
      />

      <OnboardingChecklist />

      <section className="space-y-4">
        <SectionHeader
          title="Sample prompts"
          description="Copy text into the relevant form — nothing is submitted automatically."
        />
        <div className="grid gap-4 lg:grid-cols-2">
          {SAMPLE_PROMPTS.map((sample) => (
            <Card key={sample.title}>
              <CardHeader>
                <CardTitle className="text-base">{sample.title}</CardTitle>
                <CardDescription>{sample.target}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <pre className="bg-muted max-h-40 overflow-auto rounded-md p-3 text-xs whitespace-pre-wrap">
                  {sample.prompt}
                </pre>
                <div className="flex flex-wrap gap-2">
                  <CopyPromptButton text={sample.prompt} />
                  <Button type="button" size="sm" variant="secondary" asChild>
                    <a href={sample.href}>Go to {sample.target.toLowerCase()}</a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
