import * as React from "react";

import { CopyButton } from "@/components/data-display/copy-button";
import { cn } from "@/lib/utils/cn";

export interface CodeBlockProps extends React.HTMLAttributes<HTMLDivElement> {
  code: string;
  language?: string;
  maxHeight?: string;
}

function CodeBlock({ code, language, maxHeight = "24rem", className, ...props }: CodeBlockProps) {
  return (
    <div className={cn("bg-muted/40 relative rounded-md border", className)} {...props}>
      <div className="absolute top-2 right-2 z-10 flex items-center gap-2">
        {language ? (
          <span className="text-muted-foreground text-xs uppercase">{language}</span>
        ) : null}
        <CopyButton value={code} aria-label="Copy code" />
      </div>
      <pre
        className="overflow-auto p-4 pr-12 font-mono text-xs leading-relaxed"
        style={{ maxHeight }}
      >
        <code>{code}</code>
      </pre>
    </div>
  );
}

export { CodeBlock };
