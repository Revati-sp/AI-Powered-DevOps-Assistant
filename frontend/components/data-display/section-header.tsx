import * as React from "react";

import { cn } from "@/lib/utils/cn";

export interface SectionHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

function SectionHeader({ title, description, actions, className, ...props }: SectionHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
      {...props}
    >
      <div className="space-y-0.5">
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        {description ? <p className="text-muted-foreground text-sm">{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}

export { SectionHeader };
