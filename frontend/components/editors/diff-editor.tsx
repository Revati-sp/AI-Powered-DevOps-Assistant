"use client";

import dynamic from "next/dynamic";
import { useTheme } from "next-themes";

import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils/cn";
import type { EditorLanguage } from "@/components/editors/code-editor";

const MonacoDiffEditor = dynamic(
  () => import("@monaco-editor/react").then((mod) => mod.DiffEditor),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full min-h-[200px] items-center justify-center">
        <Spinner />
      </div>
    ),
  },
);

export interface DiffEditorProps {
  original: string;
  modified: string;
  language?: EditorLanguage;
  readOnly?: boolean;
  height?: string | number;
  className?: string;
}

function DiffEditor({
  original,
  modified,
  language = "plaintext",
  readOnly = true,
  height = "400px",
  className,
}: DiffEditorProps) {
  const { resolvedTheme } = useTheme();
  const theme = resolvedTheme === "dark" ? "vs-dark" : "light";

  return (
    <div className={cn("overflow-hidden rounded-md border", className)}>
      <MonacoDiffEditor
        original={original}
        modified={modified}
        language={language}
        theme={theme}
        height={height}
        options={{
          readOnly,
          minimap: { enabled: false },
          wordWrap: "on",
          scrollBeyondLastLine: false,
          automaticLayout: true,
          fontSize: 13,
          renderSideBySide: true,
        }}
      />
    </div>
  );
}

export { DiffEditor };
