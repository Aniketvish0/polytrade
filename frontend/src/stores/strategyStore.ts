import { create } from 'zustand';
import type { Strategy } from '@/types/ws';
import { apiClient } from '@/api/client';

interface StrategyStore {
  strategies: Strategy[];

  setStrategies: (strategies: Strategy[]) => void;
  updateStrategy: (id: string, updates: Partial<Strategy>) => void;
  fetchStrategies: () => Promise<void>;
}

export const useStrategyStore = create<StrategyStore>((set) => ({
  strategies: [],

  setStrategies: (strategies) => set({ strategies }),

  updateStrategy: (id, updates) =>
    set((state) => ({
      strategies: state.strategies.map((s) =>
        s.id === id ? { ...s, ...updates } : s
      ),
    })),

  fetchStrategies: async () => {
    try {
      const data = await apiClient.get<Strategy[]>('/api/strategies');
      set({ strategies: data });
    } catch {
      // no strategies yet
    }
  },
}));
