import { create } from 'zustand';
import type { Policy } from '@/types/ws';

interface PolicyStore {
  policies: Policy[];

  setPolicies: (policies: Policy[]) => void;
  updatePolicy: (id: string, updates: Partial<Policy>) => void;
  togglePolicy: (id: string) => void;
}

const defaultPolicies: Policy[] = [
  {
    id: 'policy-1',
    name: 'MAX_POSITION_SIZE',
    description: 'Maximum position size per market',
    enabled: true,
    parameters: { maxShares: 1000, maxValue: 500 },
  },
  {
    id: 'policy-2',
    name: 'DAILY_TRADE_LIMIT',
    description: 'Maximum number of trades per day',
    enabled: true,
    parameters: { maxTrades: 50 },
  },
  {
    id: 'policy-3',
    name: 'VOLATILITY_GATE',
    description: 'Pause trading during high volatility',
    enabled: true,
    parameters: { threshold: 0.15 },
  },
  {
    id: 'policy-4',
    name: 'CONCENTRATION_LIMIT',
    description: 'Maximum portfolio concentration in single market',
    enabled: false,
    parameters: { maxPercent: 25 },
  },
];

export const usePolicyStore = create<PolicyStore>((set) => ({
  policies: defaultPolicies,

  setPolicies: (policies) => set({ policies }),

  updatePolicy: (id, updates) =>
    set((state) => ({
      policies: state.policies.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ),
    })),

  togglePolicy: (id) =>
    set((state) => ({
      policies: state.policies.map((p) =>
        p.id === id ? { ...p, enabled: !p.enabled } : p
      ),
    })),
}));
