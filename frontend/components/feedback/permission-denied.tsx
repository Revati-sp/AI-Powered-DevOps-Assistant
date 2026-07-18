import * as React from "react";
import { ShieldOff } from "lucide-react";

import { EmptyState } from "@/components/feedback/empty-state";
import { cn } from "@/lib/utils/cn";

export interface PermissionDeniedProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}

function PermissionDenied({
  title = "Permission denied",
  description = "You do not have access to view this resource.",
  action,
  className,
  ...props
}: PermissionDeniedProps) {
  return (
    <EmptyState
      icon={<ShieldOff />}
      title={title}
      description={description}
      action={action}
      className={cn(className)}
      {...props}
    />
  );
}

export { PermissionDenied };
