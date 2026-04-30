import { useEffect } from 'react';
import {
  RefreshCw,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { useTradeStore } from '@/stores/tradeStore';
import { useAgentStore } from '@/stores/agentStore';
import { PanelHeader } from '@/components/shared/PanelHeader';
import { Badge } from '@/components/shared/Badge';
import { MonoValue } from '@/components/shared/MonoValue';
import { LiveMarkets } from '@/components/dashboard/LiveMarkets';
import { ActivityLog } from '@/components/dashboard/ActivityLog';
import { formatUSD, formatOdds, formatRelativeTime, truncate } from '@/utils/format';
import type { AgentStatus } from '@/types/agent';

const statusIndicator: Record<string, { color: string; label: string }> = {
  scanning: { color: 'bg-blue-400', label: 'Scanning Markets' },
  researching: { color: 'bg-violet-400', label: 'Researching' },
  analyzing: { color: 'bg-amber-400', label: 'Analyzing' },
  trading: { color: 'bg-emerald-400', label: 'Trading' },
  running: { color: 'bg-emerald-400', label: 'Running' },
  idle: { color: 'bg-zinc-500', label: 'Idle' },
  paused: { color: 'bg-yellow-500', label: 'Paused' },
  offline: { color: 'bg-red-500', label: 'Offline' },
  error: { color: 'bg-red-500', label: 'Error' },
  disconnected: { color: 'bg-zinc-600', label: 'Disconnected' },
};

function getIndicator(status: AgentStatus) {
  return statusIndicator[status] ?? { color: 'bg-zinc-600', label: status };
}

export function PipelinePage() {
  const trades = useTradeStore((s) => s.trades);
  const pendingApprovals = useTradeStore((s) => s.pendingApprovals);
  const approveTradeAction = useTradeStore((s) => s.approveTradeAction);
  const rejectTradeAction = useTradeStore((s) => s.rejectTradeAction);
  const fetchTrades = useTradeStore((s) => s.fetchTrades);
  const fetchApprovals = useTradeStore((s) => s.fetchApprovals);

  const status = useAgentStore((s) => s.status);
  const currentTask = useAgentStore((s) => s.currentTask);
  const fetchStatus = useAgentStore((s) => s.fetchStatus);

  useEffect(() => {
    fetchTrades();
    fetchApprovals();
    fetchStatus();
  }, [fetchTrades, fetchApprovals, fetchStatus]);

  const handleRefresh = () => {
    fetchTrades();
    fetchApprovals();
    fetchStatus();
  };

  const indicator = getIndicator(status);
  const isActive = ['scanning', 'researching', 'analyzing', 'trading', 'running'].includes(status);

  return (
    <div className="flex flex-col h-full overflow-hidden bg-base">
      {/* Agent Status Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-panel">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              {isActive && (
                <span
                  className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${indicator.color}`}
                />
              )}
              <span
                className={`relative inline-flex h-2.5 w-2.5 rounded-full ${indicator.color}`}
              />
            </span>
            <span className="text-xs font-semibold tracking-wider uppercase text-primary">
              {indicator.label}
            </span>
          </div>
          {currentTask && (
            <span className="text-xxs text-muted font-mono truncate max-w-[300px]">
              {currentTask}
            </span>
          )}
        </div>

        <button
          onClick={handleRefresh}
          className="flex items-center gap-1.5 px-2 py-1 text-xxs font-mono text-muted
                     border border-border rounded hover:bg-white/[0.04] hover:text-primary
                     transition-colors"
        >
          <RefreshCw size={10} />
          Refresh
        </button>
      </div>

      {/* Live Markets (top section) */}
      <div className="h-[35%] min-h-[200px] border-b border-border">
        <LiveMarkets />
      </div>

      {/* Three column layout */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left: Activity Log */}
        <div className="flex-[2] flex flex-col min-h-0 border-r border-border">
          <ActivityLog />
        </div>

        {/* Center: Trade History */}
        <div className="flex-[3] flex flex-col min-h-0 border-r border-border">
          <PanelHeader
            label="Trade History"
            icon={<Activity size={11} />}
            actions={
              <span className="font-mono text-xxs text-muted">
                {trades.length} trades
              </span>
            }
          />

          <div className="flex-1 overflow-y-auto min-h-0">
            {trades.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <span className="text-xs text-muted">No trades yet</span>
              </div>
            ) : (
              <div className="divide-y divide-border/50">
                {trades.map((trade) => {
                  const isBuy = trade.action === 'buy' || trade.side === 'YES';
                  return (
                    <div
                      key={trade.id}
                      className="px-3 py-2.5 hover:bg-white/[0.02] transition-colors"
                    >
                      {/* Row 1: Market question + badge */}
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-1.5 min-w-0">
                          {isBuy ? (
                            <ArrowUpRight size={12} className="text-approved shrink-0" />
                          ) : (
                            <ArrowDownRight size={12} className="text-denied shrink-0" />
                          )}
                          <span className="text-xs text-primary truncate">
                            {trade.market_question}
                          </span>
                        </div>
                        <Badge status={trade.enforcement_result} className="shrink-0" />
                      </div>

                      {/* Row 2: Trade details */}
                      <div className="flex items-center gap-3 mt-1 ml-[18px]">
                        <MonoValue
                          value={`${trade.shares} ${trade.side} @ ${formatOdds(trade.price)}`}
                          size="xs"
                          className="text-muted"
                        />
                        <MonoValue
                          value={formatUSD(trade.total_amount)}
                          size="xs"
                          className="text-secondary"
                        />
                      </div>

                      {/* Row 3: Confidence, edge, sources */}
                      <div className="flex items-center gap-3 mt-1 ml-[18px]">
                        {trade.confidence_score != null && (
                          <span className="text-xxs text-muted">
                            Conf:{' '}
                            <span className="font-mono text-primary">
                              {(trade.confidence_score * 100).toFixed(0)}%
                            </span>
                          </span>
                        )}
                        {trade.edge != null && (
                          <span className="text-xxs text-muted">
                            Edge:{' '}
                            <span className="font-mono text-primary">
                              {(trade.edge * 100).toFixed(1)}%
                            </span>
                          </span>
                        )}
                        {trade.sources_count != null && (
                          <span className="text-xxs text-muted">
                            Sources:{' '}
                            <span className="font-mono text-primary">
                              {trade.sources_count}
                            </span>
                          </span>
                        )}
                      </div>

                      {/* Row 4: Reasoning */}
                      {trade.reasoning && (
                        <div className="mt-1 ml-[18px]">
                          <span className="text-xxs text-muted italic">
                            {truncate(trade.reasoning, 100)}
                          </span>
                        </div>
                      )}

                      {/* Row 5: Timestamp */}
                      <div className="mt-1 ml-[18px]">
                        <span className="text-xxs text-muted font-mono">
                          {trade.executed_at
                            ? formatRelativeTime(new Date(trade.executed_at).getTime())
                            : ''}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right: Pending Approvals */}
        <div className="flex-[2] flex flex-col min-h-0">
          <PanelHeader
            label="Pending Approvals"
            icon={<Clock size={11} />}
            actions={
              <span className="font-mono text-xxs text-muted">
                {pendingApprovals.length} pending
              </span>
            }
          />

          <div className="flex-1 overflow-y-auto min-h-0">
            {pendingApprovals.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <span className="text-xs text-muted">No pending approvals</span>
              </div>
            ) : (
              <div className="divide-y divide-border/50">
                {pendingApprovals.map((approval) => {
                  const isBuy = approval.action === 'buy' || approval.side === 'YES';
                  return (
                    <div
                      key={approval.id}
                      className="px-3 py-2.5 hover:bg-white/[0.02] transition-colors"
                    >
                      {/* Market question + held badge */}
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-1.5 min-w-0">
                          {isBuy ? (
                            <ArrowUpRight size={12} className="text-approved shrink-0" />
                          ) : (
                            <ArrowDownRight size={12} className="text-denied shrink-0" />
                          )}
                          <span className="text-xs text-primary truncate">
                            {approval.market_question}
                          </span>
                        </div>
                        <Badge status="held" className="shrink-0" />
                      </div>

                      {/* Trade details */}
                      <div className="flex items-center gap-3 mt-1 ml-[18px]">
                        <MonoValue
                          value={`${approval.shares} ${approval.side} @ ${formatOdds(approval.price)}`}
                          size="xs"
                          className="text-muted"
                        />
                        <MonoValue
                          value={formatUSD(approval.total_amount)}
                          size="xs"
                          className="text-secondary"
                        />
                      </div>

                      {/* Confidence + threshold */}
                      <div className="flex items-center gap-3 mt-1 ml-[18px]">
                        {approval.confidence_score != null && (
                          <span className="text-xxs text-muted">
                            Conf:{' '}
                            <span className="font-mono text-primary">
                              {(approval.confidence_score * 100).toFixed(0)}%
                            </span>
                          </span>
                        )}
                        {approval.threshold_breached && (
                          <span className="text-xxs text-held font-mono">
                            Threshold: {approval.threshold_breached}
                          </span>
                        )}
                      </div>

                      {/* Reasoning */}
                      {approval.reasoning && (
                        <div className="mt-1 ml-[18px]">
                          <span className="text-xxs text-muted italic">
                            {truncate(approval.reasoning, 100)}
                          </span>
                        </div>
                      )}

                      {/* Expires + created */}
                      <div className="flex items-center gap-3 mt-1 ml-[18px]">
                        <span className="text-xxs text-muted font-mono">
                          Created{' '}
                          {formatRelativeTime(new Date(approval.created_at).getTime())}
                        </span>
                        <span className="text-xxs text-held font-mono">
                          Expires{' '}
                          {new Date(approval.expires_at).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                            hour12: false,
                          })}
                        </span>
                      </div>

                      {/* Approve / Deny buttons */}
                      <div className="flex items-center gap-2 mt-2 ml-[18px]">
                        <button
                          onClick={() => approveTradeAction(approval.id)}
                          className="flex items-center gap-1 px-2.5 py-1 text-xxs font-semibold
                                     font-mono uppercase tracking-wider
                                     bg-approved/10 text-approved border border-approved/30
                                     rounded hover:bg-approved/20 transition-colors"
                        >
                          <CheckCircle2 size={10} />
                          Approve
                        </button>
                        <button
                          onClick={() => rejectTradeAction(approval.id)}
                          className="flex items-center gap-1 px-2.5 py-1 text-xxs font-semibold
                                     font-mono uppercase tracking-wider
                                     bg-denied/10 text-denied border border-denied/30
                                     rounded hover:bg-denied/20 transition-colors"
                        >
                          <XCircle size={10} />
                          Deny
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
