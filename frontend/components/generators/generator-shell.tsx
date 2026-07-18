"use client";

import type { ReactNode } from "react";

import { PageHeader } from "@/components/data-display/page-header";
import { cn } from "@/lib/utils/cn";

export type GeneratorShellProps = {
  title: string;
  description?: string;
  form: ReactNode;
  output: ReactNode;
  className?: string;
};

/**
 * Two-panel layout: form inputs | generated output.
 */
export function GeneratorShell({
  title,
  description,
  form,
  output,
  className,
}: GeneratorShellProps) {
  return (
    <div className={cn("space-y-6", className)}>
      <PageHeader title={title} description={description} />
      <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
        <section className="min-w-0 space-y-4">{form}</section>
        <section className="min-w-0 space-y-4 lg:sticky lg:top-4">{output}</section>
      </div>
    </div>
  );
}
