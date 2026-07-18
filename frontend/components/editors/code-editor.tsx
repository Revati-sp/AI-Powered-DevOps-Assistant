"use client";

import dynamic from "next/dynamic";
import { useTheme } from "next-themes";

import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils/cn";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[200px] items-center justify-center">
      <Spinner />
    </div>
  ),
});

export type EditorLanguage =
  "dockerfile" | "yaml" | "json" | "shell" | "markdown" | "plaintext" | "hcl" | "groovy";

export interface CodeEditorProps {
  value: string;
  onChange?: (value: string | undefined) => void;
  language?: EditorLanguage;
  readOnly?: boolean;
  height?: string | number;
  className?: string;
  path?: string;
}

function CodeEditor({
  value,
  onChange,
  language = "plaintext",
  readOnly = false,
  height = "400px",
  className,
  path,
}: CodeEditorProps) {
  const { resolvedTheme } = useTheme();
  const theme = resolvedTheme === "dark" ? "vs-dark" : "light";

  return (
    <div className={cn("overflow-hidden rounded-md border", className)}>
      <MonacoEditor
        value={value}
        onChange={onChange}
        language={language}
        theme={theme}
        height={height}
        path={path}
        options={{
          readOnly,
          minimap: { enabled: false },
          wordWrap: "on",
          scrollBeyondLastLine: false,
          automaticLayout: true,
          fontSize: 13,
          tabSize: 2,
        }}
      />
    </div>
  );
}

export { CodeEditor };
