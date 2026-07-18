import * as React from "react";

import { cn } from "@/lib/utils/cn";

export interface PageHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  breadcrumbs?: React.ReactNode;
}

function PageHeader({
  title,
  description,
  actions,
  breadcrumbs,
  className,
  ...props
}: PageHeaderProps) {
  return (
    <div className={cn("flex flex-col gap-4", className)} {...props}>
      {breadcrumbs}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          {description ? <p className="text-muted-foreground text-sm">{description}</p> : null}
        </div>
        {actions ? (
          <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>
        ) : null}
      </div>
    </div>
  );
}

export { PageHeader };
