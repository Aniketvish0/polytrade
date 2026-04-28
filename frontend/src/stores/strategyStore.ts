import { create } from 'zustand';
import type { Strategy } from '@/types/ws';

interface StrategyStore {
  strategies: Strategy[];

  setStrategies: (strategies: Strategy[]) => void;
  updateStrategy: (id: string, updates: Partial<Strategy>) => void;
  toggleStrategy: (id: string) => void;
}

const defaultStrategies: Strategy[] = [
  {
    id: 'strat-1',
    name: 'MOMENTUM',
    description: 'Follow market momentum signals',
    enabled: true,
    parameters: { lookback: 24, threshold: 0.05 },
  },
  {
    id: 'strat-2',
    name: 'MEAN_REVERSION',
    description: 'Trade mean reversion on overextended markets',
    enabled: true,
    parameters: { window: 48, zScore: 2.0 },
  },
  {
    id: 'strat-3',
    name: 'NEWS_SENTIMENT',
    description: 'Trade on news sentiment analysis',
    enabled: false,
    parameters: { minRelevance: 0.7, minConfidence: 0.8 },
  },
];

export const useStrategyStore = create<StrategyStore>((set) => ({
  strategies: defaultStrategies,

  setStrategies: (strategies) => set({ strategies }),

  updateStrategy: (id, updates) =>
    set((state) => ({
      strategies: state.strategies.map((s) =>
        s.id === id ? { ...s, ...updates } : s
      ),
    })),

  toggleStrategy: (id) =>
    set((state) => ({
      strategies: state.strategies.map((s) =>
        s.id === id ? { ...s, enabled: !s.enabled } : s
      ),
    })),
}));
