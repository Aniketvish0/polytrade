export type TradeStatus =
  | 'pending'
  | 'approved'
  | 'held'
  | 'denied'
  | 'executed'
  | 'blocked'
  | 'cancelled';

export type TradeSide = 'buy' | 'sell';

export interface Trade {
  id: string;
  market: string;
  outcome: string;
  side: TradeSide;
  shares: number;
  price: number;
  total: number;
  status: TradeStatus;
  reason?: string;
  policyFlags?: string[];
  timestamp: number;
}

export interface ApprovalRequest {
  id: string;
  tradeId: string;
  trade: Trade;
  reason: string;
  riskScore: number;
  policyViolations: string[];
  timestamp: number;
}
