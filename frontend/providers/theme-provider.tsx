"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import * as React from "react";

const defaultTheme =
  process.env.NEXT_PUBLIC_DEFAULT_THEME === "dark" ||
  process.env.NEXT_PUBLIC_DEFAULT_THEME === "light" ||
  process.env.NEXT_PUBLIC_DEFAULT_THEME === "system"
    ? process.env.NEXT_PUBLIC_DEFAULT_THEME
    : "system";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme={defaultTheme}
      enableSystem
      disableTransitionOnChange
    >
      {children}
    </NextThemesProvider>
  );
}
