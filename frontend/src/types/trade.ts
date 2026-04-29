export type TradeStatus =
  | 'pending'
  | 'approved'
  | 'held'
  | 'denied'
  | 'executed'
  | 'auto_approved'
  | 'blocked'
  | 'cancelled';

export type TradeSide = 'buy' | 'sell';

export interface Trade {
  id: string;
  market_id: string;
  market_question: string;
  market_category: string | null;
  action: string;
  side: string;
  shares: number;
  price: number;
  total_amount: number;
  confidence_score: number | null;
  edge: number | null;
  sources_count: number | null;
  reasoning: string | null;
  enforcement_result: string;
  armoriq_plan_hash: string | null;
  executed_at: string;
}

export interface ApprovalRequest {
  id: string;
  market_id: string;
  market_question: string;
  action: string;
  side: string;
  shares: number;
  price: number;
  total_amount: number;
  category: string | null;
  confidence_score: number | null;
  reasoning: string | null;
  sources: unknown[] | Record<string, unknown> | null;
  threshold_breached: string | null;
  status: string;
  expires_at: string;
  created_at: string;
}
