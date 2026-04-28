import { create } from 'zustand';
import type { Position, PortfolioSummary } from '@/types/portfolio';

interface PortfolioStore {
  summary: PortfolioSummary;
  positions: Position[];

  setSummary: (summary: PortfolioSummary) => void;
  setPositions: (positions: Position[]) => void;
  updatePosition: (position: Position) => void;
  removePosition: (id: string) => void;
}

const defaultSummary: PortfolioSummary = {
  totalValue: 25420.5,
  totalPnl: 1842.3,
  totalPnlPercent: 7.82,
  cashBalance: 8250.0,
  positionCount: 5,
  dayPnl: 342.15,
  dayPnlPercent: 1.36,
  maxDrawdown: -3.2,
};

const mockPositions: Position[] = [
  {
    id: 'pos-1',
    market: 'Presidential Election 2024',
    outcome: 'Yes',
    shares: 500,
    avgPrice: 0.62,
    currentPrice: 0.68,
    value: 340.0,
    pnl: 30.0,
    pnlPercent: 9.68,
    timestamp: Date.now(),
  },
  {
    id: 'pos-2',
    market: 'Fed Rate Cut March',
    outcome: 'No',
    shares: 300,
    avgPrice: 0.45,
    currentPrice: 0.52,
    value: 156.0,
    pnl: 21.0,
    pnlPercent: 15.56,
    timestamp: Date.now(),
  },
  {
    id: 'pos-3',
    market: 'BTC > 100k by EOY',
    outcome: 'Yes',
    shares: 200,
    avgPrice: 0.35,
    currentPrice: 0.31,
    value: 62.0,
    pnl: -8.0,
    pnlPercent: -11.43,
    timestamp: Date.now(),
  },
  {
    id: 'pos-4',
    market: 'Supreme Court Ruling',
    outcome: 'Yes',
    shares: 750,
    avgPrice: 0.71,
    currentPrice: 0.74,
    value: 555.0,
    pnl: 22.5,
    pnlPercent: 4.23,
    timestamp: Date.now(),
  },
  {
    id: 'pos-5',
    market: 'Next Twitter CEO',
    outcome: 'Internal',
    shares: 400,
    avgPrice: 0.28,
    currentPrice: 0.33,
    value: 132.0,
    pnl: 20.0,
    pnlPercent: 17.86,
    timestamp: Date.now(),
  },
];

export const usePortfolioStore = create<PortfolioStore>((set) => ({
  summary: defaultSummary,
  positions: mockPositions,

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
}));
