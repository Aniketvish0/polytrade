import { Activity, Wifi, WifiOff, LogOut } from 'lucide-react';
import { useAgentStore } from '@/stores/agentStore';
import { useAuthStore } from '@/stores/authStore';

const statusLabels: Record<string, string> = {
  idle: 'IDLE',
  scanning: 'SCANNING',
  researching: 'RESEARCHING',
  analyzing: 'ANALYZING',
  trading: 'TRADING',
  running: 'RUNNING',
  paused: 'PAUSED',
  offline: 'OFFLINE',
  error: 'ERROR',
  disconnected: 'OFFLINE',
};

const statusDotColors: Record<string, string> = {
  idle: 'bg-approved',
  scanning: 'bg-accent',
  researching: 'bg-accent',
  analyzing: 'bg-accent',
  trading: 'bg-held',
  running: 'bg-accent',
  paused: 'bg-muted',
  offline: 'bg-muted',
  error: 'bg-denied',
  disconnected: 'bg-muted',
};

export function HeaderBar() {
  const status = useAgentStore((s) => s.status);
  const connectionState = useAgentStore((s) => s.connectionState);
  const currentTask = useAgentStore((s) => s.currentTask);
  const isConnected = connectionState === 'connected';
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <header className="flex items-center justify-between h-8 px-3 bg-panel border-b border-border shrink-0 select-none">
      <div className="flex items-center gap-3">
        <span className="font-mono text-sm font-bold tracking-widest text-primary">
          POLYTRADE
        </span>
        <span className="text-xxs text-muted font-mono">v0.1.0</span>
      </div>

      <div className="flex items-center gap-4">
        {currentTask && (
          <span className="text-xxs text-secondary font-mono truncate max-w-[200px]">
            {currentTask}
          </span>
        )}

        <div className="flex items-center gap-1.5">
          <Activity size={11} className="text-muted" />
          <div
            className={`w-1.5 h-1.5 ${statusDotColors[status] ?? 'bg-muted'} ${
              status === 'scanning' || status === 'researching' || status === 'analyzing' || status === 'trading' || status === 'running'
                ? 'pulse-dot'
                : ''
            }`}
          />
          <span className="font-mono text-xxs text-secondary tracking-wider">
            {statusLabels[status]}
          </span>
        </div>

        <div className="flex items-center gap-1">
          {isConnected ? (
            <Wifi size={11} className="text-approved" />
          ) : (
            <WifiOff size={11} className="text-denied" />
          )}
          <span className={`font-mono text-xxs ${isConnected ? 'text-approved' : 'text-denied'}`}>
            {isConnected ? 'LIVE' : 'OFF'}
          </span>
        </div>

        {user && (
          <div className="flex items-center gap-2 pl-2 border-l border-border">
            <span className="font-mono text-xxs text-secondary truncate max-w-[120px]">
              {user.display_name ?? user.email}
            </span>
            <button
              onClick={logout}
              className="text-muted hover:text-denied transition-colors"
              title="Logout"
            >
              <LogOut size={11} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
