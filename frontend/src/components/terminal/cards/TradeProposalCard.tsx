import type { ChatMessage } from '@/types/chat';
import type { ApprovalRequest } from '@/types/trade';
import { Badge } from '@/components/shared/Badge';
import { Button } from '@/components/shared/Button';
import { MonoValue } from '@/components/shared/MonoValue';
import { formatUSD, formatOdds } from '@/utils/format';
import { useTradeStore } from '@/stores/tradeStore';
import { ArrowUpRight, ArrowDownRight, Shield } from 'lucide-react';

interface TradeProposalCardProps {
  message: ChatMessage;
}

export function TradeProposalCard({ message }: TradeProposalCardProps) {
  const approval = (message.data as { approval?: ApprovalRequest })?.approval;
  const trade = (message.data as { trade?: Record<string, unknown> })?.trade;
  const approveTradeAction = useTradeStore((s) => s.approveTradeAction);
  const rejectTradeAction = useTradeStore((s) => s.rejectTradeAction);

  if (!approval && !trade) {
    return (
      <div className="px-2 py-1 bg-surface border border-border">
        <span className="text-xs text-secondary">{message.content}</span>
      </div>
    );
  }

  const marketQuestion = approval?.market_question ?? (trade?.market_question as string) ?? '';
  const side = approval?.side ?? (trade?.side as string) ?? '';
  const action = approval?.action ?? (trade?.action as string) ?? 'buy';
  const shares = approval?.shares ?? (trade?.shares as number) ?? 0;
  const price = approval?.price ?? (trade?.price as number) ?? 0;
  const totalAmount = approval?.total_amount ?? (trade?.total_amount as number) ?? 0;
  const reasoning = approval?.reasoning ?? (trade?.reasoning as string) ?? '';
  const thresholdBreached = approval?.threshold_breached;
  const status = approval?.status ?? 'pending';
  const approvalId = approval?.id;

  const isBuy = action === 'buy';
  const isPending = status === 'pending';

  const handleApprove = () => {
    if (approvalId) {
      approveTradeAction(approvalId);
    }
  };

  const handleReject = () => {
    if (approvalId) {
      rejectTradeAction(approvalId);
    }
  };

  return (
    <div className="bg-surface border border-border p-2 space-y-1.5 max-w-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {isBuy ? (
            <ArrowUpRight size={12} className="text-approved" />
          ) : (
            <ArrowDownRight size={12} className="text-denied" />
          )}
          <span className={`font-mono text-xs font-semibold ${isBuy ? 'text-approved' : 'text-denied'}`}>
            {action.toUpperCase()}
          </span>
          <Badge status={status === 'pending' ? 'held' : status} />
        </div>
      </div>

      <div className="text-xs text-primary font-medium">{marketQuestion}</div>
      <div className="text-xxs text-secondary">Side: {side}</div>

      <div className="grid grid-cols-3 gap-2 py-1">
        <div>
          <div className="text-xxs text-muted">Shares</div>
          <MonoValue value={shares} />
        </div>
        <div>
          <div className="text-xxs text-muted">Price</div>
          <MonoValue value={formatOdds(price)} />
        </div>
        <div>
          <div className="text-xxs text-muted">Total</div>
          <MonoValue value={formatUSD(totalAmount)} />
        </div>
      </div>

      {reasoning && (
        <div className="flex items-start gap-1 py-1 text-xxs text-held">
          <Shield size={10} className="shrink-0 mt-0.5" />
          <span>{reasoning}</span>
        </div>
      )}

      {thresholdBreached && (
        <div className="flex flex-wrap gap-1">
          <span className="font-mono text-xxs text-held bg-held/10 px-1 py-px">
            {thresholdBreached}
          </span>
        </div>
      )}

      {isPending && (
        <div className="flex items-center gap-2 pt-1 border-t border-border">
          <Button variant="success" size="sm" onClick={handleApprove}>
            APPROVE
          </Button>
          <Button variant="danger" size="sm" onClick={handleReject}>
            REJECT
          </Button>
        </div>
      )}
    </div>
  );
}
