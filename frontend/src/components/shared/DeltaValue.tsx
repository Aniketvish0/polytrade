import { formatUSD, formatPercent } from '@/utils/format';

interface DeltaValueProps {
  value: number;
  format?: 'usd' | 'percent' | 'raw';
  size?: 'xs' | 'sm' | 'base';
  showSign?: boolean;
  className?: string;
}

const sizeClasses = {
  xs: 'text-xxs',
  sm: 'text-xs',
  base: 'text-sm',
};

export function DeltaValue({
  value,
  format = 'usd',
  size = 'sm',
  showSign = true,
  className = '',
}: DeltaValueProps) {
  const isPositive = value > 0;
  const isZero = value === 0;

  const colorClass = isZero
    ? 'text-muted'
    : isPositive
      ? 'text-approved'
      : 'text-denied';

  let display: string;
  switch (format) {
    case 'usd':
      display = (showSign && isPositive ? '+' : '') + formatUSD(value);
      break;
    case 'percent':
      display = formatPercent(value);
      break;
    case 'raw':
      display = (showSign && isPositive ? '+' : '') + value.toFixed(2);
      break;
  }

  return (
    <span className={`font-mono ${sizeClasses[size]} tabular-nums ${colorClass} ${className}`}>
      {display}
    </span>
  );
}
