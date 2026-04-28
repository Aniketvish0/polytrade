export type AgentStatus =
  | 'idle'
  | 'analyzing'
  | 'trading'
  | 'paused'
  | 'error'
  | 'disconnected';

export type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'reconnecting';

export interface AgentState {
  status: AgentStatus;
  connectionState: ConnectionState;
  currentTask: string | null;
  uptime: number;
  lastHeartbeat: number;
}
