import { ArrowRightLeft, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { useTradeStore } from '@/stores/tradeStore';
import { PanelHeader } from '@/components/shared/PanelHeader';
import { Badge } from '@/components/shared/Badge';
import { MonoValue } from '@/components/shared/MonoValue';
import { formatUSD, formatOdds, formatRelativeTime } from '@/utils/format';

export function TradeFeed() {
  const trades = useTradeStore((s) => s.trades);

  return (
    <div className="flex flex-col h-full">
      <PanelHeader
        label="Trade Feed"
        icon={<ArrowRightLeft size={11} />}
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
              const statusForBadge = trade.enforcement_result === 'auto_approved' ? 'executed' : trade.enforcement_result;
              return (
                <div
                  key={trade.id}
                  className="flex items-center gap-2 px-3 py-1.5 hover:bg-white/[0.02] transition-colors"
                >
                  <div className="shrink-0">
                    {isBuy ? (
                      <ArrowUpRight size={12} className="text-approved" />
                    ) : (
                      <ArrowDownRight size={12} className="text-denied" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`font-mono text-xxs font-semibold ${
                          isBuy ? 'text-approved' : 'text-denied'
                        }`}
                      >
                        {trade.action?.toUpperCase() ?? 'BUY'}
                      </span>
                      <span className="text-xs text-primary truncate">
                        {trade.market_question}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-px">
                      <MonoValue
                        value={`${trade.shares} ${trade.side} @ ${formatOdds(trade.price)}`}
                        size="xs"
                        className="text-muted"
                      />
                      {trade.reasoning && (
                        <span className="text-xxs text-held truncate max-w-[150px]">
                          {trade.reasoning}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col items-end shrink-0 gap-0.5">
                    <Badge status={statusForBadge as never} />
                    <MonoValue
                      value={formatUSD(trade.total_amount)}
                      size="xs"
                      className="text-secondary"
                    />
                  </div>

                  <div className="text-xxs text-muted font-mono shrink-0 w-12 text-right">
                    {trade.executed_at ? formatRelativeTime(new Date(trade.executed_at).getTime()) : ''}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
