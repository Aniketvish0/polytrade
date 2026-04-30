import { create } from 'zustand';

export interface ActivityEntry {
  id: string;
  phase: string;
  message: string;
  timestamp: number;
  detail?: Record<string, unknown>;
}

interface ActivityStore {
  entries: ActivityEntry[];
  addEntry: (phase: string, message: string, detail?: Record<string, unknown>) => void;
  clear: () => void;
}

const MAX_ENTRIES = 200;

export const useActivityStore = create<ActivityStore>((set) => ({
  entries: [],

  addEntry: (phase, message, detail) =>
    set((state) => {
      const entry: ActivityEntry = {
        id: `act-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        phase,
        message,
        timestamp: Date.now(),
        detail,
      };
      const next = [entry, ...state.entries];
      return { entries: next.length > MAX_ENTRIES ? next.slice(0, MAX_ENTRIES) : next };
    }),

  clear: () => set({ entries: [] }),
}));
