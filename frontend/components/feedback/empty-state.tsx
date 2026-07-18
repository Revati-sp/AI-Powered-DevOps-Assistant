import * as React from "react";

import { cn } from "@/lib/utils/cn";

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

function EmptyState({ icon, title, description, action, className, ...props }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 px-6 py-12 text-center",
        className,
      )}
      {...props}
    >
      {icon ? <div className="text-muted-foreground [&_svg]:h-10 [&_svg]:w-10">{icon}</div> : null}
      <div className="space-y-1">
        <h3 className="text-foreground text-lg font-semibold">{title}</h3>
        {description ? (
          <p className="text-muted-foreground max-w-md text-sm">{description}</p>
        ) : null}
      </div>
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}

export { EmptyState };
