import { create } from 'zustand';
import type { Policy } from '@/types/ws';
import { apiClient } from '@/api/client';

interface PolicyStore {
  policies: Policy[];

  setPolicies: (policies: Policy[]) => void;
  updatePolicy: (id: string, updates: Partial<Policy>) => void;
  fetchPolicies: () => Promise<void>;
}

export const usePolicyStore = create<PolicyStore>((set) => ({
  policies: [],

  setPolicies: (policies) => set({ policies }),

  updatePolicy: (id, updates) =>
    set((state) => ({
      policies: state.policies.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ),
    })),

  fetchPolicies: async () => {
    try {
      const data = await apiClient.get<Policy[]>('/api/policies');
      set({ policies: data });
    } catch {
      // no policies yet
    }
  },
}));
