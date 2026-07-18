import * as React from "react";

import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils/cn";

export interface LoadingStateProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: string;
}

function LoadingState({ label = "Loading…", className, ...props }: LoadingStateProps) {
  return (
    <div
      className={cn("flex flex-col items-center justify-center gap-3 px-6 py-12", className)}
      {...props}
    >
      <Spinner size="lg" />
      <p className="text-muted-foreground text-sm">{label}</p>
    </div>
  );
}

export { LoadingState };
