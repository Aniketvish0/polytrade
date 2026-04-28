import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    borderRadius: {
      none: '0',
      sm: '1px',
      DEFAULT: '2px',
      md: '2px',
      lg: '2px',
      xl: '2px',
      full: '2px',
    },
    extend: {
      colors: {
        base: '#0f0f0f',
        panel: '#1a1a2e',
        surface: '#16213e',
        border: '#1e293b',
        'border-bright': '#334155',
        primary: '#e2e8f0',
        secondary: '#94a3b8',
        muted: '#64748b',
        accent: '#3b82f6',
        approved: '#22c55e',
        held: '#f59e0b',
        denied: '#ef4444',
        pending: '#3b82f6',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        xxs: ['10px', { lineHeight: '14px' }],
        xs: ['11px', { lineHeight: '16px' }],
        sm: ['12px', { lineHeight: '18px' }],
        base: ['13px', { lineHeight: '20px' }],
        md: ['14px', { lineHeight: '22px' }],
        lg: ['16px', { lineHeight: '24px' }],
        xl: ['18px', { lineHeight: '28px' }],
      },
    },
  },
  plugins: [],
} satisfies Config;
