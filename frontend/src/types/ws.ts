import type { Trade, ApprovalRequest } from './trade';
import type { Position, PortfolioSummary } from './portfolio';
import type { NewsItem } from './news';
import type { AgentStatus } from './agent';
import type { ChatMessage } from './chat';

// Backend event structure: { type: "domain:action", data: {...}, timestamp: "..." }
export interface BackendEvent {
  type: string;
  data: Record<string, unknown>;
  timestamp?: string;
}

// Internal (frontend) event types — used by dispatchServerEvent
export type ServerEvent =
  | { type: 'chat_message'; payload: ChatMessage }
  | { type: 'trade_update'; payload: Trade }
  | { type: 'approval_request'; payload: ApprovalRequest }
  | { type: 'portfolio_update'; payload: PortfolioSummary }
  | { type: 'position_update'; payload: Position }
  | { type: 'news_item'; payload: NewsItem }
  | { type: 'agent_status'; payload: { status: AgentStatus; currentTask: string | null } }
  | { type: 'heartbeat'; payload: { timestamp: number } }
  | { type: 'error'; payload: { message: string; code?: string } }
  | { type: 'policy_update'; payload: { policies: Policy[] } }
  | { type: 'strategy_update'; payload: { strategies: Strategy[] } };

export interface Policy {
  id: string;
  name: string;
  is_active: boolean;
  global_rules: Record<string, unknown>;
  category_rules: Record<string, unknown>;
  confidence_rules: Record<string, unknown>;
  risk_rules: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Strategy {
  id: string;
  name: string;
  is_active: boolean;
  priority: number;
  rules: Record<string, unknown>;
  context: string;
  created_at: string;
  updated_at: string;
}
