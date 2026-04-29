import { useAgentStore } from '@/stores/agentStore';
import { useTradeStore } from '@/stores/tradeStore';

const statusMessages: Record<string, string> = {
  idle: 'Agent ready. Type /start to begin.',
  scanning: 'Scanning markets...',
  researching: 'Researching news & data...',
  analyzing: 'Analyzing trade opportunity...',
  trading: 'Executing trade...',
  running: 'Agent running...',
  paused: 'Agent paused. Type /resume to continue.',
  offline: 'Agent offline. Type /start to begin.',
  error: 'Agent encountered an error.',
  disconnected: 'Agent disconnected.',
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

export function AgentStatusBar() {
  const status = useAgentStore((s) => s.status);
  const currentTask = useAgentStore((s) => s.currentTask);
  const pendingCount = useTradeStore((s) => s.pendingApprovals.length);

  const isPulsing = status === 'scanning' || status === 'researching' || status === 'analyzing' || status === 'trading' || status === 'running';

  return (
    <div className="flex items-center justify-between px-3 py-1 bg-panel border-b border-border shrink-0">
      <div className="flex items-center gap-2">
        <div
          className={`w-1.5 h-1.5 ${statusDotColors[status] ?? 'bg-muted'} ${
            isPulsing ? 'pulse-dot' : ''
          }`}
        />
        <span className="text-xxs text-secondary font-mono">
          {currentTask ?? statusMessages[status] ?? status}
        </span>
      </div>

      {pendingCount > 0 && (
        <div className="flex items-center gap-1">
          <span className="text-xxs font-mono text-held">
            {pendingCount} PENDING
          </span>
        </div>
      )}
    </div>
  );
}
