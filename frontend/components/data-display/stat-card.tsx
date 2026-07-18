import * as React from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils/cn";

export interface StatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: React.ReactNode;
  description?: string;
  icon?: React.ReactNode;
  trend?: React.ReactNode;
}

function StatCard({ label, value, description, icon, trend, className, ...props }: StatCardProps) {
  return (
    <Card className={cn(className)} {...props}>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <CardDescription>{label}</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums">{value}</CardTitle>
        </div>
        {icon ? <div className="text-muted-foreground [&_svg]:h-5 [&_svg]:w-5">{icon}</div> : null}
      </CardHeader>
      {(description || trend) && (
        <CardContent className="text-muted-foreground flex items-center gap-2 text-xs">
          {trend}
          {description ? <span>{description}</span> : null}
        </CardContent>
      )}
    </Card>
  );
}

export { StatCard };
