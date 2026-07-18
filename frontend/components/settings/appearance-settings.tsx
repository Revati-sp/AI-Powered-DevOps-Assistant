"use client";

import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import * as React from "react";

import { PageHeader } from "@/components/data-display/page-header";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useUiStore, type UiDensity } from "@/store/ui-store";

export function AppearanceSettings() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const sidebarCollapsed = useUiStore((s) => s.sidebarCollapsed);
  const setSidebarCollapsed = useUiStore((s) => s.setSidebarCollapsed);
  const density = useUiStore((s) => s.density);
  const setDensity = useUiStore((s) => s.setDensity);
  const reducedMotion = useUiStore((s) => s.reducedMotion);
  const setReducedMotion = useUiStore((s) => s.setReducedMotion);

  // Prefer controlled theme once next-themes has resolved on the client.
  const themeValue = theme ?? resolvedTheme ?? "system";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Appearance"
        description="Theme and layout preferences stored locally in this browser."
      />

      <div className="max-w-lg space-y-6">
        <div className="space-y-2">
          <Label htmlFor="theme">Theme</Label>
          <Select value={themeValue} onValueChange={setTheme}>
            <SelectTrigger id="theme">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="light">
                <span className="flex items-center gap-2">
                  <Sun className="h-4 w-4" /> Light
                </span>
              </SelectItem>
              <SelectItem value="dark">
                <span className="flex items-center gap-2">
                  <Moon className="h-4 w-4" /> Dark
                </span>
              </SelectItem>
              <SelectItem value="system">
                <span className="flex items-center gap-2">
                  <Monitor className="h-4 w-4" /> System
                </span>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center justify-between rounded-md border px-3 py-3">
          <div className="space-y-0.5">
            <Label htmlFor="sidebar">Collapsed sidebar</Label>
            <p className="text-muted-foreground text-xs">Prefer a narrow sidebar on desktop.</p>
          </div>
          <Switch id="sidebar" checked={sidebarCollapsed} onCheckedChange={setSidebarCollapsed} />
        </div>

        <div className="space-y-2">
          <Label htmlFor="density">Density</Label>
          <Select value={density} onValueChange={(value) => setDensity(value as UiDensity)}>
            <SelectTrigger id="density">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="comfortable">Comfortable</SelectItem>
              <SelectItem value="compact">Compact</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center justify-between rounded-md border px-3 py-3">
          <div className="space-y-0.5">
            <Label htmlFor="reduced-motion">Reduced motion</Label>
            <p className="text-muted-foreground text-xs">
              Prefer fewer animations and transitions.
            </p>
          </div>
          <Switch id="reduced-motion" checked={reducedMotion} onCheckedChange={setReducedMotion} />
        </div>
      </div>
    </div>
  );
}
