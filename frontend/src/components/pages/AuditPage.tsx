import { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Shield, Copy, Check } from 'lucide-react';
import { apiClient } from '@/api/client';
import { PanelHeader } from '@/components/shared/PanelHeader';
import { Badge } from '@/components/shared/Badge';
import { MonoValue } from '@/components/shared/MonoValue';
import { formatUSD, formatOdds, truncate } from '@/utils/format';

interface AuditEntry {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: {
    market_id: string;
    market_question: string;
    side: string;
    shares: number;
    price: number;
    total_amount: number;
    category: string;
    confidence: number;
    reasoning: string;
    enforcement_reason: string;
    threshold_breached: string | null;
  };
  armoriq_plan_hash: string | null;
  armoriq_intent_token: string | null;
  created_at: string;
}

type FilterAction = 'all' | 'auto_approve' | 'hold' | 'deny';

const filterConfig: { value: FilterAction; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'auto_approve', label: 'Approved' },
  { value: 'hold', label: 'Held' },
  { value: 'deny', label: 'Denied' },
];

/** Map action strings like "trade_auto_approve" to a Badge-compatible status */
function actionToBadgeStatus(action: string): string {
  if (action.includes('auto_approve')) return 'auto_approved';
  if (action.includes('hold')) return 'held';
  if (action.includes('deny')) return 'denied';
  return action;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-0.5 text-muted hover:text-primary transition-colors"
      title="Copy to clipboard"
    >
      {copied ? <Check size={10} className="text-approved" /> : <Copy size={10} />}
    </button>
  );
}

export function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<FilterAction>('all');

  const fetchAudit = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filter !== 'all') {
        params.action = `trade_${filter}`;
      }
      const data = await apiClient.get<AuditEntry[]>('/api/audit', params);
      setEntries(data);
    } catch {
      // audit logs may not be available yet
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchAudit();
  }, [fetchAudit]);

  const filteredEntries = entries;

  return (
    <div className="flex flex-col h-full overflow-hidden bg-base">
      {/* Header */}
      <PanelHeader
        label="ArmorIQ Audit Trail"
        icon={<Shield size={11} />}
        actions={
          <div className="flex items-center gap-2">
            <span className="font-mono text-xxs text-muted">
              {filteredEntries.length} entries
            </span>
            <button
              onClick={fetchAudit}
              disabled={loading}
              className="flex items-center gap-1.5 px-2 py-1 text-xxs font-mono text-muted
                         border border-border rounded hover:bg-white/[0.04] hover:text-primary
                         transition-colors disabled:opacity-40"
            >
              <RefreshCw size={10} className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>
        }
      />

      {/* Filter bar */}
      <div className="flex items-center gap-1.5 px-3 py-2 border-b border-border bg-panel">
        {filterConfig.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-2 py-0.5 text-xxs font-mono font-semibold tracking-wider uppercase
                         rounded border transition-colors
                         ${
                           filter === f.value
                             ? 'bg-accent/10 text-accent border-accent/30'
                             : 'text-muted border-border hover:bg-white/[0.04] hover:text-primary'
                         }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Audit log list */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {filteredEntries.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-xs text-muted">
              {loading ? 'Loading audit logs...' : 'No audit entries found'}
            </span>
          </div>
        ) : (
          <div className="divide-y divide-border/50">
            {filteredEntries.map((entry) => (
              <AuditCard key={entry.id} entry={entry} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AuditCard({ entry }: { entry: AuditEntry }) {
  const { details } = entry;
  const badgeStatus = actionToBadgeStatus(entry.action);
  const hasProof = entry.armoriq_plan_hash || entry.armoriq_intent_token;
  const timestamp = new Date(entry.created_at);

  return (
    <div className="px-4 py-3 hover:bg-white/[0.02] transition-colors">
      {/* Row 1: Action badge + market question + timestamp */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Badge status={badgeStatus} className="shrink-0" />
          <span className="text-xs text-primary truncate">
            {details.market_question}
          </span>
        </div>
        <span className="text-xxs text-muted font-mono shrink-0">
          {timestamp.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
          })}{' '}
          {timestamp.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
          })}
        </span>
      </div>

      {/* Row 2: Trade details */}
      <div className="flex items-center gap-3 mt-1.5">
        <MonoValue
          value={`${details.shares} ${details.side} @ ${formatOdds(details.price)}`}
          size="xs"
          className="text-muted"
        />
        <MonoValue
          value={formatUSD(details.total_amount)}
          size="xs"
          className="text-secondary"
        />
        {details.confidence != null && (
          <span className="text-xxs text-muted">
            Conf:{' '}
            <span className="font-mono text-primary">
              {(details.confidence * 100).toFixed(0)}%
            </span>
          </span>
        )}
        {details.category && (
          <span className="text-xxs text-muted font-mono">
            {details.category}
          </span>
        )}
      </div>

      {/* Row 3: Enforcement reason */}
      {details.enforcement_reason && (
        <div className="mt-1.5">
          <span className="text-xxs text-held italic">
            {truncate(details.enforcement_reason, 200)}
          </span>
        </div>
      )}

      {/* Row 4: ArmorIQ Proof section */}
      {hasProof && (
        <div className="mt-2 border-l-2 border-accent pl-3 py-1.5 bg-accent/5 rounded-r">
          <div className="flex items-center gap-1.5 mb-1">
            <Shield size={10} className="text-accent" />
            <span className="text-xxs font-semibold tracking-wider uppercase text-accent">
              ArmorIQ Proof
            </span>
          </div>

          {entry.armoriq_plan_hash && (
            <div className="flex items-center gap-1.5 mt-1">
              <span className="text-xxs text-muted w-20 shrink-0">Plan Hash</span>
              <MonoValue
                value={truncate(entry.armoriq_plan_hash, 24)}
                size="xs"
                className="text-primary"
              />
              <CopyButton text={entry.armoriq_plan_hash} />
            </div>
          )}

          {entry.armoriq_intent_token && (
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="text-xxs text-muted w-20 shrink-0">Intent Token</span>
              <MonoValue
                value={truncate(entry.armoriq_intent_token, 24)}
                size="xs"
                className="text-primary"
              />
              <CopyButton text={entry.armoriq_intent_token} />
            </div>
          )}

          {details.threshold_breached && (
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="text-xxs text-muted w-20 shrink-0">Threshold</span>
              <MonoValue
                value={details.threshold_breached}
                size="xs"
                className="text-held"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
