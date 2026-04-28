interface MonoValueProps {
  value: string | number;
  className?: string;
  size?: 'xs' | 'sm' | 'base' | 'lg';
}

const sizeClasses = {
  xs: 'text-xxs',
  sm: 'text-xs',
  base: 'text-sm',
  lg: 'text-base',
};

export function MonoValue({ value, className = '', size = 'sm' }: MonoValueProps) {
  return (
    <span className={`font-mono ${sizeClasses[size]} tabular-nums ${className}`}>
      {value}
    </span>
  );
}
