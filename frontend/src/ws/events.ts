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

export const CLIENT_EVENTS = {
  SEND_MESSAGE: 'send_message',
  APPROVE_TRADE: 'approve_trade',
  DENY_TRADE: 'deny_trade',
  PAUSE_AGENT: 'pause_agent',
  RESUME_AGENT: 'resume_agent',
  UPDATE_POLICY: 'update_policy',
  UPDATE_STRATEGY: 'update_strategy',
} as const;
