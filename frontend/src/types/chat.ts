export type MessageRole = 'user' | 'agent' | 'system';

export type MessageType =
  | 'text'
  | 'trade_proposal'
  | 'approval_request'
  | 'news_summary'
  | 'policy_confirm'
  | 'error';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  type: MessageType;
  content: string;
  data?: Record<string, unknown>;
  timestamp: number;
}

export interface CommandHistoryEntry {
  command: string;
  timestamp: number;
}
