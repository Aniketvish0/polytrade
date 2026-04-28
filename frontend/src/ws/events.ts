// Legacy frontend event types
export const WS_EVENTS = {
  CHAT_MESSAGE: 'chat_message',
  TRADE_UPDATE: 'trade_update',
  APPROVAL_REQUEST: 'approval_request',
  PORTFOLIO_UPDATE: 'portfolio_update',
  POSITION_UPDATE: 'position_update',
  NEWS_ITEM: 'news_item',
  AGENT_STATUS: 'agent_status',
  HEARTBEAT: 'heartbeat',
  ERROR: 'error',
  POLICY_UPDATE: 'policy_update',
  STRATEGY_UPDATE: 'strategy_update',
} as const;

export type WSEventType = (typeof WS_EVENTS)[keyof typeof WS_EVENTS];

// Backend event types (domain:action format)
export const BACKEND_EVENTS = {
  AGENT_STATUS: 'agent:status',
  AGENT_MESSAGE: 'agent:message',
  TRADE_EXECUTED: 'trade:executed',
  TRADE_HELD: 'trade:held',
  TRADE_DENIED: 'trade:denied',
  PORTFOLIO_UPDATE: 'portfolio:update',
  NEWS_ITEM: 'news:item',
  POLICY_UPDATED: 'policy:updated',
  STRATEGY_UPDATED: 'strategy:updated',
  PONG: 'pong',
  APPROVAL_APPROVED: 'approval:approved',
  APPROVAL_REJECTED: 'approval:rejected',
  ERROR: 'error',
} as const;

// Client -> Server event types (what the frontend sends)
export const CLIENT_EVENTS = {
  CHAT_MESSAGE: 'chat:message',
  TRADE_APPROVE: 'trade:approve',
  TRADE_REJECT: 'trade:reject',
  PING: 'ping',
} as const;
