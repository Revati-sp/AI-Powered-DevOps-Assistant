import * as React from "react";

import { CopyButton } from "@/components/data-display/copy-button";
import { cn } from "@/lib/utils/cn";

export interface JsonViewerProps extends React.HTMLAttributes<HTMLDivElement> {
  data: unknown;
  maxHeight?: string;
}

function formatJson(data: unknown): string {
  try {
    return JSON.stringify(data, null, 2);
  } catch {
    return String(data);
  }
}

function JsonViewer({ data, maxHeight = "24rem", className, ...props }: JsonViewerProps) {
  const text = formatJson(data);

  return (
    <div className={cn("bg-muted/40 relative rounded-md border", className)} {...props}>
      <div className="absolute top-2 right-2 z-10">
        <CopyButton value={text} aria-label="Copy JSON" />
      </div>
      <pre
        className="overflow-auto p-4 pr-12 font-mono text-xs leading-relaxed"
        style={{ maxHeight }}
      >
        {text}
      </pre>
    </div>
  );
}

export { JsonViewer };
