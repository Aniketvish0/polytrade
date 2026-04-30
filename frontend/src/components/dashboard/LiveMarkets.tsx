import { useCallback, useEffect, useRef, useState } from 'react';
import { BarChart3, ChevronDown } from 'lucide-react';
import { marketsApi } from '@/api';
import { PanelHeader } from '@/components/shared/PanelHeader';
import { MonoValue } from '@/components/shared/MonoValue';
import { formatOdds, truncate } from '@/utils/format';
import type { EnhancedMarket } from '@/types/market';

const SORT_OPTIONS = [
  { value: 'score', label: 'Score' },
  { value: 'volume', label: 'Volume' },
  { value: 'edge', label: 'Edge' },
  { value: 'liquidity', label: 'Liquidity' },
] as const;

const REFRESH_INTERVAL = 15_000;

function ResearchDot({ status }: { status: EnhancedMarket['research_status'] }) {
  if (status === 'researched') {
    return <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400" title="Researched" />;
  }
  if (status === 'stale') {
    return <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400" title="Stale" />;
  }
  return <span className="inline-block w-1.5 h-1.5 rounded-full bg-zinc-600" title="Pending" />;
}

function formatVolume(v: number | null): string {
  if (v == null) return '-';
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

function formatHours(h: number | null): string {
  if (h == null) return '-';
  if (h < 1) return '<1h';
  if (h < 24) return `${h.toFixed(0)}h`;
  if (h < 168) return `${(h / 24).toFixed(0)}d`;
  return `${(h / 168).toFixed(0)}w`;
}

export function LiveMarkets() {
  const [markets, setMarkets] = useState<EnhancedMarket[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('score');
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  const fetchMarkets = useCallback(async () => {
    try {
      const data = await marketsApi.listEnhanced({
        category: category || undefined,
        sort_by: sortBy,
        limit: 50,
      });
      setMarkets(data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [category, sortBy]);

  useEffect(() => {
    setLoading(true);
    fetchMarkets();
    timerRef.current = setInterval(fetchMarkets, REFRESH_INTERVAL);
    return () => clearInterval(timerRef.current);
  }, [fetchMarkets]);

  const categories = [...new Set(markets.map((m) => m.category).filter(Boolean))] as string[];

  return (
    <div className="flex flex-col min-h-0 h-full">
      <PanelHeader
        label="Live Markets"
        icon={<BarChart3 size={11} />}
        actions={
          <span className="font-mono text-xxs text-muted">
            {markets.length} markets
          </span>
        }
      />

      {/* Filter row */}
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-border bg-panel">
        <div className="relative">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="appearance-none bg-transparent text-xxs font-mono text-muted
                       border border-border rounded px-2 py-0.5 pr-5
                       hover:text-primary focus:outline-none focus:border-zinc-500"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <ChevronDown size={10} className="absolute right-1.5 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
        </div>

        <div className="relative">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="appearance-none bg-transparent text-xxs font-mono text-muted
                       border border-border rounded px-2 py-0.5 pr-5
                       hover:text-primary focus:outline-none focus:border-zinc-500"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>Sort: {o.label}</option>
            ))}
          </select>
          <ChevronDown size={10} className="absolute right-1.5 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto min-h-0">
        {loading && markets.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-xs text-muted">Loading markets...</span>
          </div>
        ) : markets.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-xs text-muted">No markets available</span>
          </div>
        ) : (
          <table className="w-full text-xxs">
            <thead className="sticky top-0 bg-panel z-10">
              <tr className="text-left text-muted uppercase tracking-wider font-semibold">
                <th className="px-2 py-1.5 font-semibold w-[40%]">Market</th>
                <th className="px-1.5 py-1.5 font-semibold">YES</th>
                <th className="px-1.5 py-1.5 font-semibold">Edge</th>
                <th className="px-1.5 py-1.5 font-semibold">Vol</th>
                <th className="px-1.5 py-1.5 font-semibold">Liq</th>
                <th className="px-1.5 py-1.5 font-semibold text-center">Res</th>
                <th className="px-1.5 py-1.5 font-semibold">Score</th>
                <th className="px-1.5 py-1.5 font-semibold">Exp</th>
                <th className="px-1.5 py-1.5 font-semibold">Pos</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {markets.map((m) => (
                <tr
                  key={m.condition_id}
                  className={`hover:bg-white/[0.02] transition-colors ${
                    m.user_has_position ? 'bg-blue-500/[0.04]' : ''
                  }`}
                >
                  <td className="px-2 py-1">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="text-primary truncate" title={m.question}>
                        {truncate(m.question, 40)}
                      </span>
                      {m.category && (
                        <span className="text-muted font-mono shrink-0">{m.category}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-1.5 py-1">
                    <MonoValue
                      value={m.yes_price != null ? formatOdds(m.yes_price) : '-'}
                      size="xs"
                      className="text-primary"
                    />
                  </td>
                  <td className="px-1.5 py-1">
                    <MonoValue
                      value={m.edge_potential != null ? `${(m.edge_potential * 100).toFixed(0)}%` : '-'}
                      size="xs"
                      className={
                        (m.edge_potential ?? 0) > 0.6 ? 'text-emerald-400' :
                        (m.edge_potential ?? 0) > 0.3 ? 'text-amber-400' : 'text-muted'
                      }
                    />
                  </td>
                  <td className="px-1.5 py-1">
                    <MonoValue
                      value={formatVolume(m.volume != null ? Number(m.volume) : null)}
                      size="xs"
                      className="text-muted"
                    />
                  </td>
                  <td className="px-1.5 py-1">
                    <MonoValue
                      value={m.liquidity_score != null ? `${(m.liquidity_score * 100).toFixed(0)}%` : '-'}
                      size="xs"
                      className="text-muted"
                    />
                  </td>
                  <td className="px-1.5 py-1 text-center">
                    <ResearchDot status={m.research_status} />
                  </td>
                  <td className="px-1.5 py-1">
                    <MonoValue
                      value={m.composite_score != null ? m.composite_score.toFixed(3) : '-'}
                      size="xs"
                      className={
                        (m.composite_score ?? 0) > 0.6 ? 'text-emerald-400' :
                        (m.composite_score ?? 0) > 0.4 ? 'text-amber-400' : 'text-muted'
                      }
                    />
                  </td>
                  <td className="px-1.5 py-1">
                    <MonoValue
                      value={formatHours(m.hours_to_resolution)}
                      size="xs"
                      className="text-muted"
                    />
                  </td>
                  <td className="px-1.5 py-1">
                    {m.user_has_position ? (
                      <span className={`font-mono font-semibold ${
                        m.position_side === 'YES' ? 'text-emerald-400' : 'text-rose-400'
                      }`}>
                        {m.position_side}
                      </span>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
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
