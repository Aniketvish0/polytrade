import { useEffect, useRef } from 'react';
import { Scroll } from 'lucide-react';
import { useActivityStore, type ActivityEntry } from '@/stores/activityStore';
import { PanelHeader } from '@/components/shared/PanelHeader';

const phaseColors: Record<string, string> = {
  scan: 'text-blue-400',
  research: 'text-violet-400',
  analyze: 'text-amber-400',
  rank: 'text-orange-400',
  trade: 'text-emerald-400',
  cycle: 'text-zinc-400',
};

const phaseLabels: Record<string, string> = {
  scan: 'SCAN',
  research: 'RSRCH',
  analyze: 'ANALY',
  rank: 'RANK',
  trade: 'TRADE',
  cycle: 'CYCLE',
};

function formatTime(ts: number): string {
  const d = new Date(ts);
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
}

function EntryRow({ entry }: { entry: ActivityEntry }) {
  const color = phaseColors[entry.phase] ?? 'text-zinc-500';
  const label = phaseLabels[entry.phase] ?? entry.phase.toUpperCase().slice(0, 5);

  return (
    <div className="flex items-start gap-2 px-2.5 py-1 hover:bg-white/[0.02] font-mono text-xxs leading-relaxed">
      <span className="text-zinc-600 shrink-0 w-[58px]">{formatTime(entry.timestamp)}</span>
      <span className={`shrink-0 w-[38px] font-semibold ${color}`}>{label}</span>
      <span className="text-secondary break-words min-w-0">{entry.message}</span>
      {entry.detail?.confidence != null && (
        <span className="text-muted shrink-0 ml-auto">
          {((entry.detail.confidence as number) * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}

export function ActivityLog() {
  const entries = useActivityStore((s) => s.entries);
  const clear = useActivityStore((s) => s.clear);
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    if (el.scrollTop < 80) {
      el.scrollTop = 0;
    }
  }, [entries.length]);

  return (
    <div className="flex flex-col h-full">
      <PanelHeader
        label="Activity Log"
        icon={<Scroll size={11} />}
        actions={
          <div className="flex items-center gap-2">
            <span className="font-mono text-xxs text-muted">{entries.length} events</span>
            {entries.length > 0 && (
              <button
                onClick={clear}
                className="text-xxs text-muted hover:text-primary transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        }
      />
      <div ref={containerRef} className="flex-1 overflow-y-auto min-h-0">
        {entries.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-xs text-muted">Waiting for agent activity…</span>
          </div>
        ) : (
          <div className="divide-y divide-border/30">
            {entries.map((entry) => (
              <EntryRow key={entry.id} entry={entry} />
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
