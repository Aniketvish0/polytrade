import { create } from 'zustand';
import type { Position, PortfolioSummary } from '@/types/portfolio';
import { apiClient } from '@/api/client';

interface PortfolioStore {
  summary: PortfolioSummary | null;
  positions: Position[];
  isLoading: boolean;

  setSummary: (summary: PortfolioSummary) => void;
  setPositions: (positions: Position[]) => void;
  updatePosition: (position: Position) => void;
  removePosition: (id: string) => void;
  fetchPortfolio: () => Promise<void>;
  fetchPositions: () => Promise<void>;
}

export const usePortfolioStore = create<PortfolioStore>((set) => ({
  summary: null,
  positions: [],
  isLoading: false,

  setSummary: (summary) => set({ summary }),

  setPositions: (positions) => set({ positions }),

  updatePosition: (position) =>
    set((state) => ({
      positions: state.positions.map((p) =>
        p.id === position.id ? position : p
      ),
    })),

  removePosition: (id) =>
    set((state) => ({
      positions: state.positions.filter((p) => p.id !== id),
    })),

  fetchPortfolio: async () => {
    try {
      set({ isLoading: true });
      const raw = await apiClient.get<Record<string, unknown>>('/api/portfolio');
      const summary: PortfolioSummary = {
        id: raw.id as string,
        balance: Number(raw.balance),
        total_deposited: Number(raw.total_deposited),
        total_pnl: Number(raw.total_pnl),
        total_trades: Number(raw.total_trades),
        winning_trades: Number(raw.winning_trades),
        losing_trades: Number(raw.losing_trades),
        win_rate: Number(raw.win_rate),
        open_positions: Number(raw.open_positions),
        today_pnl: Number(raw.today_pnl),
        today_trades: Number(raw.today_trades),
        daily_spend_used: Number(raw.daily_spend_used),
        daily_spend_limit: Number(raw.daily_spend_limit),
      };
      set({ summary, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchPositions: async () => {
    try {
      const raw = await apiClient.get<Record<string, unknown>[]>('/api/portfolio/positions');
      const positions: Position[] = raw.map((p) => ({
        id: p.id as string,
        market_id: p.market_id as string,
        market_question: p.market_question as string,
        market_category: (p.market_category as string) ?? null,
        side: p.side as string,
        shares: Number(p.shares),
        avg_price: Number(p.avg_price),
        current_price: p.current_price != null ? Number(p.current_price) : null,
        current_value: p.current_value != null ? Number(p.current_value) : null,
        unrealized_pnl: p.unrealized_pnl != null ? Number(p.unrealized_pnl) : null,
        cost_basis: Number(p.cost_basis),
        status: p.status as string,
        opened_at: p.opened_at as string,
      }));
      set({ positions });
    } catch {
      // no positions yet
    }
  },
}));
