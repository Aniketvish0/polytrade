import type { ChatMessage } from '@/types/chat';
import type { Trade } from '@/types/trade';
import { Badge } from '@/components/shared/Badge';
import { Button } from '@/components/shared/Button';
import { MonoValue } from '@/components/shared/MonoValue';
import { formatUSD, formatOdds } from '@/utils/format';
import { useTradeStore } from '@/stores/tradeStore';
import { wsClient } from '@/ws/client';
import { ArrowUpRight, ArrowDownRight, Shield } from 'lucide-react';

interface TradeProposalCardProps {
  message: ChatMessage;
}

export function TradeProposalCard({ message }: TradeProposalCardProps) {
  const trade = (message.data as { trade?: Trade })?.trade;
  const updateTrade = useTradeStore((s) => s.updateTrade);
  const removeApproval = useTradeStore((s) => s.removeApproval);

  if (!trade) {
    return (
      <div className="px-2 py-1 bg-surface border border-border">
        <span className="text-xs text-secondary">{message.content}</span>
      </div>
    );
  }

  const isBuy = trade.side === 'buy';
  const isHeld = trade.status === 'held';

  const handleApprove = () => {
    wsClient.send({ type: 'approve_trade', payload: { tradeId: trade.id } });
    updateTrade(trade.id, { status: 'approved' });
    removeApproval(trade.id);
  };

  const handleReject = () => {
    wsClient.send({ type: 'deny_trade', payload: { tradeId: trade.id } });
    updateTrade(trade.id, { status: 'denied' });
    removeApproval(trade.id);
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
            {trade.side.toUpperCase()}
          </span>
          <Badge status={trade.status} />
        </div>
      </div>

      <div className="text-xs text-primary font-medium">{trade.market}</div>
      <div className="text-xxs text-secondary">Outcome: {trade.outcome}</div>

      <div className="grid grid-cols-3 gap-2 py-1">
        <div>
          <div className="text-xxs text-muted">Shares</div>
          <MonoValue value={trade.shares} />
        </div>
        <div>
          <div className="text-xxs text-muted">Price</div>
          <MonoValue value={formatOdds(trade.price)} />
        </div>
        <div>
          <div className="text-xxs text-muted">Total</div>
          <MonoValue value={formatUSD(trade.total)} />
        </div>
      </div>

      {trade.reason && (
        <div className="flex items-start gap-1 py-1 text-xxs text-held">
          <Shield size={10} className="shrink-0 mt-0.5" />
          <span>{trade.reason}</span>
        </div>
      )}

      {trade.policyFlags && trade.policyFlags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {trade.policyFlags.map((flag) => (
            <span
              key={flag}
              className="font-mono text-xxs text-held bg-held/10 px-1 py-px"
            >
              {flag}
            </span>
          ))}
        </div>
      )}

      {isHeld && (
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
