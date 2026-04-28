export const colors = {
  base: '#0f0f0f',
  panel: '#1a1a2e',
  surface: '#16213e',
  border: '#1e293b',
  borderBright: '#334155',
  primary: '#e2e8f0',
  secondary: '#94a3b8',
  muted: '#64748b',
  accent: '#3b82f6',
  approved: '#22c55e',
  held: '#f59e0b',
  denied: '#ef4444',
  pending: '#3b82f6',
} as const;

export const fonts = {
  sans: "'Inter', system-ui, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const fontSizes = {
  xxs: '10px',
  xs: '11px',
  sm: '12px',
  base: '13px',
  md: '14px',
  lg: '16px',
  xl: '18px',
} as const;

export const spacing = {
  px: '1px',
  0.5: '2px',
  1: '4px',
  1.5: '6px',
  2: '8px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
  8: '32px',
  10: '40px',
  12: '48px',
} as const;

export const statusColors = {
  approved: colors.approved,
  held: colors.held,
  denied: colors.denied,
  pending: colors.pending,
  blocked: colors.denied,
  executed: colors.approved,
  cancelled: colors.muted,
} as const;
