"use client";

import * as React from "react";
import { Download } from "lucide-react";

import { Button, type ButtonProps } from "@/components/ui/button";
import { sanitizeFilename } from "@/lib/utils/filename";
import { cn } from "@/lib/utils/cn";

export interface DownloadButtonProps extends Omit<ButtonProps, "onClick" | "content"> {
  content: string | Blob;
  filename: string;
  mimeType?: string;
}

function DownloadButton({
  content,
  filename,
  mimeType = "text/plain;charset=utf-8",
  className,
  children,
  ...props
}: DownloadButtonProps) {
  function handleDownload() {
    const safeName = sanitizeFilename(filename);
    const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = safeName;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Button
      type="button"
      variant="outline"
      className={cn(className)}
      onClick={handleDownload}
      {...props}
    >
      <Download />
      {children ?? "Download"}
    </Button>
  );
}

export { DownloadButton };
