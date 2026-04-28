import type { TradeStatus } from '@/types/trade';

interface BadgeProps {
  status: TradeStatus;
  className?: string;
}

const statusConfig: Record<TradeStatus, { bg: string; text: string; label: string }> = {
  approved: { bg: 'bg-approved/15', text: 'text-approved', label: 'APPROVED' },
  held: { bg: 'bg-held/15', text: 'text-held', label: 'HELD' },
  denied: { bg: 'bg-denied/15', text: 'text-denied', label: 'DENIED' },
  pending: { bg: 'bg-pending/15', text: 'text-pending', label: 'PENDING' },
  executed: { bg: 'bg-approved/15', text: 'text-approved', label: 'EXECUTED' },
  blocked: { bg: 'bg-denied/15', text: 'text-denied', label: 'BLOCKED' },
  cancelled: { bg: 'bg-muted/15', text: 'text-muted', label: 'CANCELLED' },
};

export function Badge({ status, className = '' }: BadgeProps) {
  const config = statusConfig[status];
  return (
    <span
      className={`
        inline-flex items-center px-1.5 py-px
        font-mono text-xxs font-semibold tracking-wider uppercase
        ${config.bg} ${config.text}
        border border-current/20
        ${className}
      `}
    >
      {config.label}
    </span>
  );
}
