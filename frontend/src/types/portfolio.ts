export interface Position {
  id: string;
  market_id: string;
  market_question: string;
  market_category: string | null;
  side: string;
  shares: number;
  avg_price: number;
  current_price: number | null;
  current_value: number | null;
  unrealized_pnl: number | null;
  cost_basis: number;
  status: string;
  opened_at: string;
}

export interface PortfolioSummary {
  id: string;
  balance: number;
  total_deposited: number;
  total_pnl: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  open_positions: number;
  today_pnl: number;
  today_trades: number;
  daily_spend_used: number;
  daily_spend_limit: number;
}
