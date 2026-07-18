import * as React from "react";

import { cn } from "@/lib/utils/cn";

export interface FilterBarProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  actions?: React.ReactNode;
}

function FilterBar({ children, actions, className, ...props }: FilterBarProps) {
  return (
    <div
      className={cn("flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between", className)}
      {...props}
    >
      <div className="flex flex-1 flex-wrap items-end gap-2">{children}</div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}

export { FilterBar };
