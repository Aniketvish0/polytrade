import { create } from 'zustand';

export type LayoutMode = 'split' | 'terminal' | 'dashboard';
export type AppPage = 'chat' | 'dashboard' | 'pipeline' | 'strategies' | 'audit';

interface UIStore {
  layoutMode: LayoutMode;
  splitRatio: number;
  isMobile: boolean;
  isDragging: boolean;
  activePage: AppPage;

  setLayoutMode: (mode: LayoutMode) => void;
  setSplitRatio: (ratio: number) => void;
  setIsMobile: (isMobile: boolean) => void;
  setIsDragging: (isDragging: boolean) => void;
  setActivePage: (page: AppPage) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  layoutMode: 'split',
  splitRatio: 0.45,
  isMobile: false,
  isDragging: false,
  activePage: 'chat',

  setLayoutMode: (mode) => set({ layoutMode: mode }),
  setSplitRatio: (ratio) => set({ splitRatio: Math.max(0.2, Math.min(0.8, ratio)) }),
  setIsMobile: (isMobile) => set({ isMobile }),
  setIsDragging: (isDragging) => set({ isDragging }),
  setActivePage: (page) => set({ activePage: page }),
}));
