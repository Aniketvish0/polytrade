import { create } from 'zustand';
import type { Trade, ApprovalRequest } from '@/types/trade';

interface TradeStore {
  trades: Trade[];
  pendingApprovals: ApprovalRequest[];

  addTrade: (trade: Trade) => void;
  updateTrade: (id: string, updates: Partial<Trade>) => void;
  setTrades: (trades: Trade[]) => void;
  addApproval: (approval: ApprovalRequest) => void;
  removeApproval: (id: string) => void;
  setApprovals: (approvals: ApprovalRequest[]) => void;
}

const mockTrades: Trade[] = [
  {
    id: 'trade-1',
    market: 'Presidential Election 2024',
    outcome: 'Yes',
    side: 'buy',
    shares: 100,
    price: 0.65,
    total: 65.0,
    status: 'executed',
    timestamp: Date.now() - 300000,
  },
  {
    id: 'trade-2',
    market: 'Fed Rate Cut March',
    outcome: 'No',
    side: 'buy',
    shares: 50,
    price: 0.48,
    total: 24.0,
    status: 'approved',
    timestamp: Date.now() - 180000,
  },
  {
    id: 'trade-3',
    market: 'BTC > 100k by EOY',
    outcome: 'Yes',
    side: 'sell',
    shares: 75,
    price: 0.33,
    total: 24.75,
    status: 'held',
    reason: 'Position size exceeds daily limit',
    policyFlags: ['MAX_POSITION_SIZE'],
    timestamp: Date.now() - 60000,
  },
  {
    id: 'trade-4',
    market: 'Supreme Court Ruling',
    outcome: 'Yes',
    side: 'buy',
    shares: 200,
    price: 0.72,
    total: 144.0,
    status: 'denied',
    reason: 'Market volatility too high',
    timestamp: Date.now() - 30000,
  },
  {
    id: 'trade-5',
    market: 'Next Twitter CEO',
    outcome: 'Internal',
    side: 'buy',
    shares: 150,
    price: 0.31,
    total: 46.5,
    status: 'pending',
    timestamp: Date.now() - 5000,
  },
];

export const useTradeStore = create<TradeStore>((set) => ({
  trades: mockTrades,
  pendingApprovals: [
    {
      id: 'approval-1',
      tradeId: 'trade-3',
      trade: mockTrades[2],
      reason: 'Position size exceeds daily limit',
      riskScore: 72,
      policyViolations: ['MAX_POSITION_SIZE', 'DAILY_TRADE_LIMIT'],
      timestamp: Date.now() - 60000,
    },
  ],

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
}));
