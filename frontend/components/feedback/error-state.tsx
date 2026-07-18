import * as React from "react";
import { AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";

export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  message: string;
  requestId?: string;
  retryAfterSeconds?: number;
  onRetry?: () => void;
}

function ErrorState({
  title = "Something went wrong",
  message,
  requestId,
  retryAfterSeconds,
  onRetry,
  className,
  ...props
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center justify-center gap-3 px-6 py-12 text-center",
        className,
      )}
      {...props}
    >
      <AlertCircle className="text-destructive h-10 w-10" aria-hidden />
      <div className="space-y-1">
        <h3 className="text-foreground text-lg font-semibold">{title}</h3>
        <p className="text-muted-foreground max-w-md text-sm">{message}</p>
        {requestId ? (
          <p className="text-muted-foreground font-mono text-xs">Request ID: {requestId}</p>
        ) : null}
        {retryAfterSeconds !== undefined ? (
          <p className="text-muted-foreground text-xs">
            Try again in {retryAfterSeconds} second{retryAfterSeconds === 1 ? "" : "s"}.
          </p>
        ) : null}
      </div>
      {onRetry ? (
        <Button type="button" variant="outline" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}

export { ErrorState };
