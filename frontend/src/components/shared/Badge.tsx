interface BadgeProps {
  status: string;
  className?: string;
}

const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
  approved: { bg: 'bg-approved/15', text: 'text-approved', label: 'APPROVED' },
  auto_approved: { bg: 'bg-approved/15', text: 'text-approved', label: 'AUTO' },
  held: { bg: 'bg-held/15', text: 'text-held', label: 'HELD' },
  deny: { bg: 'bg-denied/15', text: 'text-denied', label: 'DENIED' },
  denied: { bg: 'bg-denied/15', text: 'text-denied', label: 'DENIED' },
  pending: { bg: 'bg-pending/15', text: 'text-pending', label: 'PENDING' },
  executed: { bg: 'bg-approved/15', text: 'text-approved', label: 'EXECUTED' },
  blocked: { bg: 'bg-denied/15', text: 'text-denied', label: 'BLOCKED' },
  cancelled: { bg: 'bg-muted/15', text: 'text-muted', label: 'CANCELLED' },
};

const fallback = { bg: 'bg-muted/15', text: 'text-muted', label: 'UNKNOWN' };

export function Badge({ status, className = '' }: BadgeProps) {
  const config = statusConfig[status] ?? fallback;
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
