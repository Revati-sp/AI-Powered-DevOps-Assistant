import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="from-background via-background to-primary/5 flex min-h-svh flex-col items-center justify-center bg-gradient-to-b px-6 py-16 text-center">
      <div className="border-primary/20 bg-card max-w-md rounded-xl border p-8 shadow-sm">
        <p className="text-primary mb-2 text-xs font-semibold tracking-[0.2em] uppercase">404</p>
        <h1 className="text-foreground text-2xl font-semibold tracking-tight">Page not found</h1>
        <p className="text-muted-foreground mt-2 text-sm">
          The page you requested doesn&apos;t exist or may have moved.
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Button asChild>
            <Link href="/dashboard">Go to dashboard</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/login">Sign in</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
