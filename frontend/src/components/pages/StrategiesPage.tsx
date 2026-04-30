import { useEffect, useState } from 'react';
import { useStrategyStore } from '@/stores/strategyStore';
import { usePolicyStore } from '@/stores/policyStore';
import { strategiesApi, policiesApi } from '@/api';
import { PanelHeader } from '@/components/shared/PanelHeader';
import { MonoValue } from '@/components/shared/MonoValue';
import type { Strategy, Policy } from '@/types/ws';

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function ActiveBadge({ active }: { active: boolean }) {
  return (
    <span
      className={`
        inline-flex items-center px-1.5 py-px
        font-mono text-xxs font-semibold tracking-wider uppercase
        border border-current/20
        ${active ? 'bg-approved/15 text-approved' : 'bg-muted/15 text-muted'}
      `}
    >
      {active ? 'ACTIVE' : 'INACTIVE'}
    </span>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return <span className="text-xxs text-muted uppercase tracking-wider">{children}</span>;
}

function KV({ label, value, mono = true }: { label: string; value: unknown; mono?: boolean }) {
  const display = value === undefined || value === null ? '--' : String(value);
  return (
    <div className="flex items-center justify-between py-0.5">
      <Label>{label}</Label>
      {mono ? (
        <MonoValue value={display} size="xs" className="text-primary" />
      ) : (
        <span className="text-xs text-primary">{display}</span>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Strategy Card                                                     */
/* ------------------------------------------------------------------ */

function StrategyCard({
  strategy,
  onToggle,
  toggling,
}: {
  strategy: Strategy;
  onToggle: (id: string) => void;
  toggling: string | null;
}) {
  const rules = strategy.rules as Record<string, unknown>;
  const nested = (rules.entry_criteria ?? {}) as Record<string, unknown>;
  const entryCriteria = {
    min_confidence: nested.min_confidence ?? rules.min_confidence,
    min_edge: nested.min_edge ?? rules.min_edge,
    min_sources: nested.min_sources ?? rules.min_sources,
  } as Record<string, unknown>;
  const nestedPos = (rules.position_sizing ?? {}) as Record<string, unknown>;
  const positionSizing = {
    max_trade_amount: nestedPos.max_trade_amount ?? nestedPos.max_trade ?? rules.max_trade_amount,
    kelly_fraction: nestedPos.kelly_fraction,
  } as Record<string, unknown>;
  const categories = rules.categories as string[] | undefined;

  return (
    <div className="bg-panel border border-border p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-primary">{strategy.name}</span>
          <ActiveBadge active={strategy.is_active} />
        </div>
        <MonoValue
          value={`P${strategy.priority}`}
          size="xs"
          className="text-accent"
        />
      </div>

      {/* Context */}
      {strategy.context && (
        <p className="text-xs text-secondary mb-3 leading-relaxed">
          {strategy.context}
        </p>
      )}

      {/* Rules breakdown */}
      <div className="border-t border-border pt-2 mb-2">
        <Label>Entry Criteria</Label>
        <div className="mt-1 space-y-0.5">
          <KV label="Min Confidence" value={entryCriteria.min_confidence} />
          <KV label="Min Edge" value={entryCriteria.min_edge} />
          <KV label="Min Sources" value={entryCriteria.min_sources} />
        </div>
      </div>

      <div className="border-t border-border pt-2 mb-2">
        <Label>Position Sizing</Label>
        <div className="mt-1 space-y-0.5">
          <KV label="Max Trade Amount" value={positionSizing.max_trade_amount} />
          {positionSizing.kelly_fraction !== undefined && (
            <KV label="Kelly Fraction" value={positionSizing.kelly_fraction} />
          )}
        </div>
      </div>

      {/* Categories */}
      {categories && categories.length > 0 && (
        <div className="border-t border-border pt-2 mb-2">
          <Label>Categories</Label>
          <div className="mt-1 flex flex-wrap gap-1">
            {categories.map((cat) => (
              <span
                key={cat}
                className="inline-flex px-1.5 py-px text-xxs font-mono text-accent bg-accent/10 border border-accent/20"
              >
                {cat}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Toggle + timestamps */}
      <div className="border-t border-border pt-3 mt-3 flex items-center justify-between">
        <div className="space-y-0.5">
          <div className="text-xxs text-muted">
            Created {formatDate(strategy.created_at)}
          </div>
          <div className="text-xxs text-muted">
            Updated {formatDate(strategy.updated_at)}
          </div>
        </div>
        <button
          onClick={() => onToggle(strategy.id)}
          disabled={toggling === strategy.id}
          className={`
            px-3 py-1 text-xxs font-mono font-semibold uppercase tracking-wider
            border transition-colors
            ${
              strategy.is_active
                ? 'border-denied/40 text-denied hover:bg-denied/10'
                : 'border-approved/40 text-approved hover:bg-approved/10'
            }
            disabled:opacity-40 disabled:cursor-not-allowed
          `}
        >
          {toggling === strategy.id
            ? '...'
            : strategy.is_active
              ? 'Deactivate'
              : 'Activate'}
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Category Rules Visualization                                      */
/* ------------------------------------------------------------------ */

function CategoryRuleCard({
  category,
  rule,
}: {
  category: string;
  rule: Record<string, unknown>;
}) {
  const enabled = rule.enabled as boolean | undefined;
  const autoApproveBelow = rule.auto_approve_below as number | undefined;
  const holdAbove = rule.hold_above as number | undefined;
  const denyAbove = rule.deny_above as number | undefined;
  const maxDailySpend = rule.max_daily_spend as number | undefined;

  return (
    <div className="bg-base border border-border p-2.5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-primary capitalize">
          {category.replace(/_/g, ' ')}
        </span>
        <span
          className={`text-xxs font-mono font-semibold ${
            enabled !== false ? 'text-approved' : 'text-muted'
          }`}
        >
          {enabled !== false ? 'ON' : 'OFF'}
        </span>
      </div>
      <div className="flex gap-1.5 mb-2">
        {autoApproveBelow !== undefined && (
          <div className="flex-1 bg-approved/8 border border-approved/20 px-1.5 py-1 text-center">
            <div className="text-xxs text-muted mb-0.5">Auto-approve</div>
            <MonoValue
              value={`< $${autoApproveBelow}`}
              size="xs"
              className="text-approved"
            />
          </div>
        )}
        {holdAbove !== undefined && (
          <div className="flex-1 bg-held/8 border border-held/20 px-1.5 py-1 text-center">
            <div className="text-xxs text-muted mb-0.5">Hold</div>
            <MonoValue
              value={`> $${holdAbove}`}
              size="xs"
              className="text-held"
            />
          </div>
        )}
        {denyAbove !== undefined && (
          <div className="flex-1 bg-denied/8 border border-denied/20 px-1.5 py-1 text-center">
            <div className="text-xxs text-muted mb-0.5">Deny</div>
            <MonoValue
              value={`> $${denyAbove}`}
              size="xs"
              className="text-denied"
            />
          </div>
        )}
      </div>
      {maxDailySpend !== undefined && (
        <KV label="Max Daily Spend" value={`$${maxDailySpend}`} />
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Policy Card                                                       */
/* ------------------------------------------------------------------ */

function PolicyCard({
  policy,
  onToggle,
  toggling,
}: {
  policy: Policy;
  onToggle: (id: string) => void;
  toggling: string | null;
}) {
  const globalRules = policy.global_rules as Record<string, unknown>;
  const categoryRules = policy.category_rules as Record<string, Record<string, unknown>>;
  const confidenceRules = policy.confidence_rules as Record<string, unknown>;
  const highConfBonus = confidenceRules.high_confidence_bonus as Record<string, unknown> | undefined;

  return (
    <div className="bg-panel border border-border p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-primary">{policy.name}</span>
          <ActiveBadge active={policy.is_active} />
        </div>
      </div>

      {/* Global Rules */}
      <div className="border-t border-border pt-2 mb-2">
        <Label>Global Rules</Label>
        <div className="mt-1 space-y-0.5">
          <KV label="Max Single Trade" value={(globalRules.max_single_trade ?? globalRules.max_per_trade) != null ? `$${globalRules.max_single_trade ?? globalRules.max_per_trade}` : undefined} />
          <KV label="Daily Spend Limit" value={(globalRules.daily_spend_limit ?? globalRules.daily_limit) != null ? `$${globalRules.daily_spend_limit ?? globalRules.daily_limit}` : undefined} />
          <KV label="Max Open Positions" value={globalRules.max_open_positions} />
        </div>
      </div>

      {/* Category Rules */}
      {categoryRules && Object.keys(categoryRules).length > 0 && (
        <div className="border-t border-border pt-2 mb-2">
          <Label>Category Rules</Label>
          <div className="mt-2 grid gap-2">
            {Object.entries(categoryRules).map(([cat, rule]) => (
              <CategoryRuleCard
                key={cat}
                category={cat}
                rule={rule as Record<string, unknown>}
              />
            ))}
          </div>
        </div>
      )}

      {/* Confidence Rules */}
      <div className="border-t border-border pt-2 mb-2">
        <Label>Confidence Rules</Label>
        <div className="mt-1 space-y-0.5">
          <KV label="Min Confidence" value={confidenceRules.min_confidence} />
          <KV label="Min Sources" value={confidenceRules.min_sources} />
          {highConfBonus && (
            <>
              <div className="mt-1">
                <Label>High Confidence Bonus</Label>
              </div>
              <KV label="Threshold" value={highConfBonus.threshold} />
              <KV label="Multiplier" value={highConfBonus.multiplier} />
              <KV
                label="Max Amount"
                value={
                  highConfBonus.max_amount != null
                    ? `$${highConfBonus.max_amount}`
                    : undefined
                }
              />
            </>
          )}
        </div>
      </div>

      {/* Toggle + timestamps */}
      <div className="border-t border-border pt-3 mt-3 flex items-center justify-between">
        <div className="space-y-0.5">
          <div className="text-xxs text-muted">
            Created {formatDate(policy.created_at)}
          </div>
          <div className="text-xxs text-muted">
            Updated {formatDate(policy.updated_at)}
          </div>
        </div>
        <button
          onClick={() => onToggle(policy.id)}
          disabled={toggling === policy.id}
          className={`
            px-3 py-1 text-xxs font-mono font-semibold uppercase tracking-wider
            border transition-colors
            ${
              policy.is_active
                ? 'border-denied/40 text-denied hover:bg-denied/10'
                : 'border-approved/40 text-approved hover:bg-approved/10'
            }
            disabled:opacity-40 disabled:cursor-not-allowed
          `}
        >
          {toggling === policy.id
            ? '...'
            : policy.is_active
              ? 'Deactivate'
              : 'Activate'}
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                              */
/* ------------------------------------------------------------------ */

export function StrategiesPage() {
  const { strategies, fetchStrategies } = useStrategyStore();
  const { policies, fetchPolicies } = usePolicyStore();
  const [togglingStrategy, setTogglingStrategy] = useState<string | null>(null);
  const [togglingPolicy, setTogglingPolicy] = useState<string | null>(null);

  useEffect(() => {
    fetchStrategies();
    fetchPolicies();
  }, [fetchStrategies, fetchPolicies]);

  const handleToggleStrategy = async (id: string) => {
    setTogglingStrategy(id);
    try {
      await strategiesApi.toggle(id);
      await fetchStrategies();
    } finally {
      setTogglingStrategy(null);
    }
  };

  const handleTogglePolicy = async (id: string) => {
    setTogglingPolicy(id);
    try {
      await policiesApi.toggle(id);
      await fetchPolicies();
    } finally {
      setTogglingPolicy(null);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden bg-base">
      <div className="flex-1 min-h-0 overflow-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 h-full">
          {/* Left Column: Strategies */}
          <div className="flex flex-col min-h-0 overflow-hidden border-r border-border">
            <PanelHeader label="Strategies" />
            <div className="flex-1 overflow-auto p-4 space-y-4">
              {strategies.length === 0 && (
                <div className="text-xs text-muted font-mono text-center py-8">
                  No strategies configured
                </div>
              )}
              {strategies.map((s) => (
                <StrategyCard
                  key={s.id}
                  strategy={s}
                  onToggle={handleToggleStrategy}
                  toggling={togglingStrategy}
                />
              ))}
            </div>
          </div>

          {/* Right Column: Policies */}
          <div className="flex flex-col min-h-0 overflow-hidden">
            <PanelHeader label="Policies" />
            <div className="flex-1 overflow-auto p-4 space-y-4">
              {policies.length === 0 && (
                <div className="text-xs text-muted font-mono text-center py-8">
                  No policies configured
                </div>
              )}
              {policies.map((p) => (
                <PolicyCard
                  key={p.id}
                  policy={p}
                  onToggle={handleTogglePolicy}
                  toggling={togglingPolicy}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
