"use client";

import * as React from "react";
import { Check, Copy } from "lucide-react";

import { IconButton, type IconButtonProps } from "@/components/ui/icon-button";
import { cn } from "@/lib/utils/cn";

export interface CopyButtonProps extends Omit<
  IconButtonProps,
  "aria-label" | "onClick" | "children"
> {
  value: string;
  "aria-label"?: string;
}

function CopyButton({
  value,
  className,
  "aria-label": ariaLabel = "Copy to clipboard",
  ...props
}: CopyButtonProps) {
  const [copied, setCopied] = React.useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <IconButton
      type="button"
      variant="ghost"
      aria-label={ariaLabel}
      className={cn(className)}
      onClick={handleCopy}
      {...props}
    >
      {copied ? <Check /> : <Copy />}
    </IconButton>
  );
}

export { CopyButton };
