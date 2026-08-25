import { create } from "zustand";

type UiState = { applicationDrawerOpen: boolean; setApplicationDrawerOpen: (open: boolean) => void };

export const useUiStore = create<UiState>((set) => ({
  applicationDrawerOpen: false,
  setApplicationDrawerOpen: (applicationDrawerOpen) => set({ applicationDrawerOpen }),
}));
