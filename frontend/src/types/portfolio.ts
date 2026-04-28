export interface Position {
  id: string;
  market: string;
  outcome: string;
  shares: number;
  avgPrice: number;
  currentPrice: number;
  value: number;
  pnl: number;
  pnlPercent: number;
  timestamp: number;
}

export interface PortfolioSummary {
  totalValue: number;
  totalPnl: number;
  totalPnlPercent: number;
  cashBalance: number;
  positionCount: number;
  dayPnl: number;
  dayPnlPercent: number;
  maxDrawdown: number;
}
