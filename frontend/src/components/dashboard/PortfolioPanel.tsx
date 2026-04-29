import { Briefcase } from 'lucide-react';
import { usePortfolioStore } from '@/stores/portfolioStore';
import { PanelHeader } from '@/components/shared/PanelHeader';
import { MonoValue } from '@/components/shared/MonoValue';
import { DeltaValue } from '@/components/shared/DeltaValue';
import { formatUSD, formatOdds } from '@/utils/format';

export function PortfolioPanel() {
  const summary = usePortfolioStore((s) => s.summary);
  const positions = usePortfolioStore((s) => s.positions);
  const isLoading = usePortfolioStore((s) => s.isLoading);

  if (isLoading && !summary) {
    return (
      <div className="flex flex-col h-full">
        <PanelHeader label="Portfolio" icon={<Briefcase size={11} />} />
        <div className="flex items-center justify-center h-full">
          <span className="text-xs text-muted">Loading portfolio...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <PanelHeader
        label="Portfolio"
        icon={<Briefcase size={11} />}
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-px bg-border shrink-0">
        <StatCell label="BALANCE" value={formatUSD(summary?.balance ?? 0)} />
        <StatCell
          label="TOTAL P&L"
          value={
            <DeltaValue value={summary?.total_pnl ?? 0} format="usd" size="xs" />
          }
        />
        <StatCell
          label="WIN RATE"
          value={`${((summary?.win_rate ?? 0) * 100).toFixed(1)}%`}
        />
        <StatCell
          label="DAILY SPEND"
          value={`${formatUSD(summary?.daily_spend_used ?? 0)} / ${formatUSD(summary?.daily_spend_limit ?? 0)}`}
        />
      </div>

      {/* Positions Table */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {positions.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-xs text-muted">No open positions</span>
          </div>
        ) : (
          <table className="w-full text-left">
            <thead className="sticky top-0 bg-panel">
              <tr className="text-xxs text-muted font-mono uppercase tracking-wider">
                <th className="px-3 py-1 font-medium">Market</th>
                <th className="px-2 py-1 font-medium text-right">Shares</th>
                <th className="px-2 py-1 font-medium text-right">Avg</th>
                <th className="px-2 py-1 font-medium text-right">Price</th>
                <th className="px-2 py-1 font-medium text-right">Value</th>
                <th className="px-2 py-1 font-medium text-right">P&L</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos) => (
                <tr
                  key={pos.id}
                  className="border-t border-border/50 hover:bg-white/[0.02] transition-colors"
                >
                  <td className="px-3 py-1">
                    <div className="text-xs text-primary truncate max-w-[180px]">
                      {pos.market_question}
                    </div>
                    <div className="text-xxs text-muted">{pos.side}</div>
                  </td>
                  <td className="px-2 py-1 text-right">
                    <MonoValue value={pos.shares} size="xs" className="text-primary" />
                  </td>
                  <td className="px-2 py-1 text-right">
                    <MonoValue value={formatOdds(pos.avg_price)} size="xs" className="text-secondary" />
                  </td>
                  <td className="px-2 py-1 text-right">
                    <MonoValue value={formatOdds(pos.current_price ?? 0)} size="xs" className="text-primary" />
                  </td>
                  <td className="px-2 py-1 text-right">
                    <MonoValue value={formatUSD(pos.current_value ?? 0)} size="xs" className="text-primary" />
                  </td>
                  <td className="px-2 py-1 text-right">
                    <DeltaValue value={pos.unrealized_pnl ?? 0} format="usd" size="xs" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function StatCell({
  label,
  value,
  sub,
}: {
  label: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
}) {
  return (
    <div className="bg-panel px-3 py-1.5">
      <div className="text-xxs text-muted font-mono tracking-wider">{label}</div>
      <div className="font-mono text-xs text-primary mt-0.5">
        {typeof value === 'string' ? <MonoValue value={value} size="xs" /> : value}
      </div>
      {sub && <div className="mt-px">{sub}</div>}
    </div>
  );
}
