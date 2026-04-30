import { useEffect, useState } from 'react';
import { ShieldCheck, Clock, AlertTriangle } from 'lucide-react';
import { useTradeStore } from '@/stores/tradeStore';
import { PortfolioPanel } from '@/components/dashboard/PortfolioPanel';
import { TradeFeed } from '@/components/dashboard/TradeFeed';
import { NewsFeed } from '@/components/dashboard/NewsFeed';
import { PanelHeader } from '@/components/shared/PanelHeader';
import { Badge } from '@/components/shared/Badge';
import { MonoValue } from '@/components/shared/MonoValue';
import { formatUSD, formatOdds } from '@/utils/format';
import type { ApprovalRequest } from '@/types/trade';

function useCountdown(expiresAt: string): string {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  const diff = new Date(expiresAt).getTime() - now;
  if (diff <= 0) return 'expired';
  const mins = Math.floor(diff / 60000);
  const secs = Math.floor((diff % 60000) / 1000);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function ApprovalCard({ approval }: { approval: ApprovalRequest }) {
  const approveTradeAction = useTradeStore((s) => s.approveTradeAction);
  const rejectTradeAction = useTradeStore((s) => s.rejectTradeAction);
  const countdown = useCountdown(approval.expires_at);
  const [acting, setActing] = useState<'approve' | 'deny' | null>(null);
  const isExpired = countdown === 'expired';

  const handleApprove = async () => {
    setActing('approve');
    await approveTradeAction(approval.id);
  };

  const handleDeny = async () => {
    setActing('deny');
    await rejectTradeAction(approval.id);
  };

  return (
    <div className="px-3 py-2 hover:bg-white/[0.02] transition-colors">
      {/* Market question */}
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs text-primary truncate max-w-[220px]">
          {approval.market_question}
        </span>
        <Badge status="pending" />
      </div>

      {/* Trade details */}
      <div className="flex items-center gap-2 mt-1">
        <span
          className={`font-mono text-xxs font-semibold ${
            approval.side === 'YES' ? 'text-approved' : 'text-denied'
          }`}
        >
          {approval.side}
        </span>
        <MonoValue
          value={`${approval.shares} @ ${formatOdds(approval.price)}`}
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
      <div className="flex items-center gap-2 mt-1">
        {approval.confidence_score != null && (
          <span className="font-mono text-xxs text-muted">
            conf: {(approval.confidence_score * 100).toFixed(0)}%
          </span>
        )}
        {approval.threshold_breached && (
          <span className="flex items-center gap-0.5 text-xxs text-held">
            <AlertTriangle size={9} />
            {approval.threshold_breached}
          </span>
        )}
      </div>

      {/* Reasoning */}
      {approval.reasoning && (
        <div className="mt-1 text-xxs text-muted leading-snug line-clamp-2">
          {approval.reasoning}
        </div>
      )}

      {/* Expiry + actions */}
      <div className="flex items-center justify-between mt-2">
        <span
          className={`flex items-center gap-1 font-mono text-xxs ${
            isExpired ? 'text-denied' : 'text-muted'
          }`}
        >
          <Clock size={9} />
          {isExpired ? 'EXPIRED' : countdown}
        </span>

        <div className="flex items-center gap-1.5">
          <button
            onClick={handleApprove}
            disabled={acting !== null || isExpired}
            className="px-2 py-0.5 font-mono text-xxs font-semibold
              bg-approved/10 text-approved hover:bg-approved/20
              border border-approved/20
              disabled:opacity-40 disabled:cursor-not-allowed
              transition-colors"
          >
            {acting === 'approve' ? '...' : 'Approve'}
          </button>
          <button
            onClick={handleDeny}
            disabled={acting !== null || isExpired}
            className="px-2 py-0.5 font-mono text-xxs font-semibold
              bg-denied/10 text-denied hover:bg-denied/20
              border border-denied/20
              disabled:opacity-40 disabled:cursor-not-allowed
              transition-colors"
          >
            {acting === 'deny' ? '...' : 'Deny'}
          </button>
        </div>
      </div>
    </div>
  );
}

function PendingApprovalsPanel() {
  const pendingApprovals = useTradeStore((s) => s.pendingApprovals);

  return (
    <div className="flex flex-col h-full">
      <PanelHeader
        label="Pending Approvals"
        icon={<ShieldCheck size={11} />}
        actions={
          pendingApprovals.length > 0 ? (
            <span className="font-mono text-xxs text-pending">
              {pendingApprovals.length} pending
            </span>
          ) : undefined
        }
      />

      <div className="flex-1 overflow-y-auto min-h-0">
        {pendingApprovals.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-xs text-muted">No pending approvals</span>
          </div>
        ) : (
          <div className="divide-y divide-border/50">
            {pendingApprovals.map((approval) => (
              <ApprovalCard key={approval.id} approval={approval} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function DashboardPage() {
  const fetchTrades = useTradeStore((s) => s.fetchTrades);
  const fetchApprovals = useTradeStore((s) => s.fetchApprovals);

  useEffect(() => {
    fetchTrades();
    fetchApprovals();

    const interval = setInterval(() => {
      fetchApprovals();
    }, 10000);

    return () => clearInterval(interval);
  }, [fetchTrades, fetchApprovals]);

  return (
    <div className="flex flex-col h-full bg-base">
      {/* Top section: Portfolio — ~40% height */}
      <div className="h-[40%] border-b border-border shrink-0">
        <PortfolioPanel />
      </div>

      {/* Bottom section: Two columns — ~60% height */}
      <div className="flex flex-1 min-h-0">
        {/* Left column: Trade Feed */}
        <div className="w-1/2 border-r border-border">
          <TradeFeed />
        </div>

        {/* Right column: Pending Approvals + News Feed */}
        <div className="w-1/2 flex flex-col">
          <div className="flex-1 min-h-0 border-b border-border">
            <PendingApprovalsPanel />
          </div>
          <div className="h-[40%] shrink-0">
            <NewsFeed />
          </div>
        </div>
      </div>
    </div>
  );
}
