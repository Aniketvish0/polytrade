import { Activity, Wifi, WifiOff } from 'lucide-react';
import { useAgentStore } from '@/stores/agentStore';

const statusLabels: Record<string, string> = {
  idle: 'IDLE',
  analyzing: 'ANALYZING',
  trading: 'TRADING',
  paused: 'PAUSED',
  error: 'ERROR',
  disconnected: 'OFFLINE',
};

const statusDotColors: Record<string, string> = {
  idle: 'bg-approved',
  analyzing: 'bg-accent',
  trading: 'bg-held',
  paused: 'bg-muted',
  error: 'bg-denied',
  disconnected: 'bg-muted',
};

export function HeaderBar() {
  const status = useAgentStore((s) => s.status);
  const connectionState = useAgentStore((s) => s.connectionState);
  const currentTask = useAgentStore((s) => s.currentTask);
  const isConnected = connectionState === 'connected';

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
            className={`w-1.5 h-1.5 ${statusDotColors[status]} ${
              status === 'analyzing' || status === 'trading'
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
      </div>
    </header>
  );
}
