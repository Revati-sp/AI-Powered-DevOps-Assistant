import * as React from "react";
import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils/cn";

export interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "default" | "lg";
}

const sizeClass = {
  sm: "h-4 w-4",
  default: "h-6 w-6",
  lg: "h-8 w-8",
} as const;

function Spinner({ className, size = "default", ...props }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn("text-muted-foreground inline-flex", className)}
      {...props}
    >
      <Loader2 className={cn("animate-spin", sizeClass[size])} />
      <span className="sr-only">Loading</span>
    </div>
  );
}

export { Spinner };
