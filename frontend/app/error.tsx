"use client";

import Link from "next/link";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Avoid logging sensitive payloads; digest is safe for correlation.
    console.error("App error", error.digest ?? error.name);
  }, [error]);

  return (
    <div className="from-background via-background to-primary/5 flex min-h-svh flex-col items-center justify-center bg-gradient-to-b px-6 py-16 text-center">
      <div className="border-primary/20 bg-card max-w-md rounded-xl border p-8 shadow-sm">
        <p className="text-primary mb-2 text-xs font-semibold tracking-[0.2em] uppercase">
          Unexpected error
        </p>
        <h1 className="text-foreground text-2xl font-semibold tracking-tight">
          Something went wrong
        </h1>
        <p className="text-muted-foreground mt-2 text-sm">
          An unexpected error interrupted this page. You can retry, or return home and continue from
          there.
        </p>
        {error.digest ? (
          <p className="text-muted-foreground mt-3 font-mono text-xs">Ref: {error.digest}</p>
        ) : null}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Button type="button" onClick={reset}>
            Try again
          </Button>
          <Button type="button" variant="outline" asChild>
            <Link href="/">Go home</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
