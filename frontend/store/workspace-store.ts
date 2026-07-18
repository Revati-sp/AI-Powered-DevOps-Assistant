import { create } from "zustand";
import { persist } from "zustand/middleware";

type WorkspaceState = {
  currentOrganizationId: string | null;
  setOrganization: (organizationId: string | null) => void;
};

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      currentOrganizationId: null,
      setOrganization: (currentOrganizationId) => set({ currentOrganizationId }),
    }),
    {
      name: "ada-workspace",
      partialize: (state) => ({
        currentOrganizationId: state.currentOrganizationId,
      }),
    },
  ),
);
