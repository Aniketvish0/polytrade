import { describe, it, expect, vi } from 'vitest';
import {
  formatUSD,
  formatPercent,
  formatOdds,
  formatShares,
  formatTimestamp,
  formatRelativeTime,
  truncate,
} from '../format';

describe('formatUSD', () => {
  it('formats a positive integer', () => {
    expect(formatUSD(100)).toBe('$100.00');
  });

  it('formats zero', () => {
    expect(formatUSD(0)).toBe('$0.00');
  });

  it('formats a negative decimal', () => {
    expect(formatUSD(-50.5)).toBe('-$50.50');
  });

  it('formats a large number with commas', () => {
    expect(formatUSD(1234567.89)).toBe('$1,234,567.89');
  });
});

describe('formatPercent', () => {
  it('formats a positive value with + sign', () => {
    expect(formatPercent(5.5)).toBe('+5.50%');
  });

  it('formats zero without sign', () => {
    expect(formatPercent(0)).toBe('0.00%');
  });

  it('formats a negative value with - sign', () => {
    expect(formatPercent(-3.2)).toBe('-3.20%');
  });
});

describe('formatOdds', () => {
  it('formats a mid-range value', () => {
    expect(formatOdds(0.65)).toBe('65.0c');
  });

  it('formats zero', () => {
    expect(formatOdds(0)).toBe('0.0c');
  });

  it('formats one', () => {
    expect(formatOdds(1)).toBe('100.0c');
  });
});

describe('formatShares', () => {
  it('formats shares with comma separators', () => {
    expect(formatShares(1234)).toBe('1,234');
  });
});

describe('formatTimestamp', () => {
  it('returns HH:MM:SS format', () => {
    const result = formatTimestamp(Date.now());
    expect(result).toMatch(/^\d{2}:\d{2}:\d{2}$/);
  });
});

describe('formatRelativeTime', () => {
  it('returns seconds ago for recent timestamps', () => {
    const now = Date.now();
    expect(formatRelativeTime(now - 30_000)).toBe('30s ago');
  });

  it('returns minutes ago', () => {
    const now = Date.now();
    expect(formatRelativeTime(now - 5 * 60_000)).toBe('5m ago');
  });

  it('returns hours ago', () => {
    const now = Date.now();
    expect(formatRelativeTime(now - 3 * 3600_000)).toBe('3h ago');
  });

  it('returns days ago', () => {
    const now = Date.now();
    expect(formatRelativeTime(now - 2 * 86400_000)).toBe('2d ago');
  });
});

describe('truncate', () => {
  it('truncates a long string and adds ellipsis', () => {
    expect(truncate('hello world', 5)).toBe('hell…');
  });

  it('returns the original string when shorter than maxLen', () => {
    expect(truncate('hi', 5)).toBe('hi');
  });
});
