export type AgentStatus =
  | 'idle'
  | 'scanning'
  | 'researching'
  | 'analyzing'
  | 'trading'
  | 'running'
  | 'paused'
  | 'offline'
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
