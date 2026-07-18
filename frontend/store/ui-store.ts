import { create } from "zustand";
import { persist } from "zustand/middleware";

export type UiDensity = "comfortable" | "compact";

type UiState = {
  sidebarCollapsed: boolean;
  sidebarMobileOpen: boolean;
  commandMenuOpen: boolean;
  density: UiDensity;
  reducedMotion: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebarCollapsed: () => void;
  setSidebarMobileOpen: (open: boolean) => void;
  setCommandMenuOpen: (open: boolean) => void;
  setDensity: (density: UiDensity) => void;
  setReducedMotion: (reduced: boolean) => void;
};

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      sidebarMobileOpen: false,
      commandMenuOpen: false,
      density: "comfortable",
      reducedMotion: false,
      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
      toggleSidebarCollapsed: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarMobileOpen: (sidebarMobileOpen) => set({ sidebarMobileOpen }),
      setCommandMenuOpen: (commandMenuOpen) => set({ commandMenuOpen }),
      setDensity: (density) => set({ density }),
      setReducedMotion: (reducedMotion) => set({ reducedMotion }),
    }),
    {
      name: "ada-ui-preferences",
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        density: state.density,
        reducedMotion: state.reducedMotion,
      }),
    },
  ),
);
