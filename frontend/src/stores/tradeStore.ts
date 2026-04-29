import { create } from 'zustand';
import type { Trade, ApprovalRequest } from '@/types/trade';
import { apiClient } from '@/api/client';

interface TradeStore {
  trades: Trade[];
  pendingApprovals: ApprovalRequest[];

  addTrade: (trade: Trade) => void;
  updateTrade: (id: string, updates: Partial<Trade>) => void;
  setTrades: (trades: Trade[]) => void;
  addApproval: (approval: ApprovalRequest) => void;
  removeApproval: (id: string) => void;
  setApprovals: (approvals: ApprovalRequest[]) => void;
  fetchTrades: () => Promise<void>;
  fetchApprovals: () => Promise<void>;
  approveTradeAction: (approvalId: string) => Promise<void>;
  rejectTradeAction: (approvalId: string) => Promise<void>;
}

export const useTradeStore = create<TradeStore>((set, get) => ({
  trades: [],
  pendingApprovals: [],

  addTrade: (trade) =>
    set((state) => ({ trades: [trade, ...state.trades] })),

  updateTrade: (id, updates) =>
    set((state) => ({
      trades: state.trades.map((t) =>
        t.id === id ? { ...t, ...updates } : t
      ),
    })),

  setTrades: (trades) => set({ trades }),

  addApproval: (approval) =>
    set((state) => ({
      pendingApprovals: [approval, ...state.pendingApprovals],
    })),

  removeApproval: (id) =>
    set((state) => ({
      pendingApprovals: state.pendingApprovals.filter((a) => a.id !== id),
    })),

  setApprovals: (approvals) => set({ pendingApprovals: approvals }),

  fetchTrades: async () => {
    try {
      const raw = await apiClient.get<Record<string, unknown>[]>('/api/trades');
      const trades: Trade[] = raw.map((t) => ({
        id: t.id as string,
        market_id: t.market_id as string,
        market_question: t.market_question as string,
        market_category: (t.market_category as string) ?? null,
        action: t.action as string,
        side: t.side as string,
        shares: Number(t.shares),
        price: Number(t.price),
        total_amount: Number(t.total_amount),
        confidence_score: t.confidence_score != null ? Number(t.confidence_score) : null,
        edge: t.edge != null ? Number(t.edge) : null,
        sources_count: (t.sources_count as number) ?? null,
        reasoning: (t.reasoning as string) ?? null,
        enforcement_result: t.enforcement_result as string,
        armoriq_plan_hash: (t.armoriq_plan_hash as string) ?? null,
        executed_at: t.executed_at as string,
      }));
      set({ trades });
    } catch {
      // no trades yet
    }
  },

  fetchApprovals: async () => {
    try {
      const raw = await apiClient.get<Record<string, unknown>[]>('/api/approvals', { status: 'pending' });
      const approvals: ApprovalRequest[] = raw.map((a) => ({
        id: a.id as string,
        market_id: a.market_id as string,
        market_question: a.market_question as string,
        action: a.action as string,
        side: a.side as string,
        shares: Number(a.shares),
        price: Number(a.price),
        total_amount: Number(a.total_amount),
        category: (a.category as string) ?? null,
        confidence_score: a.confidence_score != null ? Number(a.confidence_score) : null,
        reasoning: (a.reasoning as string) ?? null,
        sources: (a.sources as unknown[] | Record<string, unknown>) ?? null,
        threshold_breached: (a.threshold_breached as string) ?? null,
        status: a.status as string,
        expires_at: a.expires_at as string,
        created_at: a.created_at as string,
      }));
      set({ pendingApprovals: approvals });
    } catch {
      // no approvals yet
    }
  },

  approveTradeAction: async (approvalId: string) => {
    try {
      await apiClient.post(`/api/approvals/${approvalId}/approve`);
      get().removeApproval(approvalId);
    } catch (err) {
      console.error('Failed to approve trade:', err);
    }
  },

  rejectTradeAction: async (approvalId: string) => {
    try {
      await apiClient.post(`/api/approvals/${approvalId}/reject`);
      get().removeApproval(approvalId);
    } catch (err) {
      console.error('Failed to reject trade:', err);
    }
  },
}));
