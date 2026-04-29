import { describe, it, expect, beforeEach, vi } from 'vitest';
import { usePortfolioStore } from '../portfolioStore';
import type { Position, PortfolioSummary } from '@/types/portfolio';

// ---------- mock fetch globally ----------
const mockFetch = vi.fn();
global.fetch = mockFetch;

function jsonResponse(body: unknown, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body)),
  });
}

const sampleSummary: PortfolioSummary = {
  id: 'p1',
  balance: 1000,
  total_deposited: 2000,
  total_pnl: 150.5,
  total_trades: 20,
  winning_trades: 12,
  losing_trades: 8,
  win_rate: 0.6,
  open_positions: 3,
  today_pnl: 25.0,
  today_trades: 5,
  daily_spend_used: 100,
  daily_spend_limit: 500,
};

const samplePosition: Position = {
  id: 'pos1',
  market_id: 'm1',
  market_question: 'Will it rain?',
  market_category: 'weather',
  side: 'yes',
  shares: 50,
  avg_price: 0.65,
  current_price: 0.7,
  current_value: 35,
  unrealized_pnl: 2.5,
  cost_basis: 32.5,
  status: 'open',
  opened_at: '2024-01-01T00:00:00Z',
};

beforeEach(() => {
  mockFetch.mockReset();
  usePortfolioStore.setState({
    summary: null,
    positions: [],
    isLoading: false,
  });
});

describe('portfolioStore', () => {
  it('has null summary and empty positions initially', () => {
    const state = usePortfolioStore.getState();
    expect(state.summary).toBeNull();
    expect(state.positions).toEqual([]);
  });

  it('setSummary updates summary', () => {
    usePortfolioStore.getState().setSummary(sampleSummary);
    expect(usePortfolioStore.getState().summary).toEqual(sampleSummary);
  });

  it('setPositions updates positions', () => {
    usePortfolioStore.getState().setPositions([samplePosition]);
    expect(usePortfolioStore.getState().positions).toEqual([samplePosition]);
  });

  it('updatePosition modifies a matching position', () => {
    usePortfolioStore.setState({ positions: [samplePosition] });
    const updated: Position = { ...samplePosition, shares: 100 };
    usePortfolioStore.getState().updatePosition(updated);
    expect(usePortfolioStore.getState().positions[0].shares).toBe(100);
  });

  it('removePosition filters out by id', () => {
    usePortfolioStore.setState({
      positions: [samplePosition, { ...samplePosition, id: 'pos2' }],
    });
    usePortfolioStore.getState().removePosition('pos1');
    const { positions } = usePortfolioStore.getState();
    expect(positions).toHaveLength(1);
    expect(positions[0].id).toBe('pos2');
  });

  it('fetchPortfolio calls API and parses Decimal fields to numbers', async () => {
    mockFetch.mockReturnValueOnce(
      jsonResponse({
        id: 'p1',
        balance: '1000.00',
        total_deposited: '2000.00',
        total_pnl: '150.50',
        total_trades: 20,
        winning_trades: 12,
        losing_trades: 8,
        win_rate: '0.60',
        open_positions: 3,
        today_pnl: '25.00',
        today_trades: 5,
        daily_spend_used: '100.00',
        daily_spend_limit: '500.00',
      })
    );

    await usePortfolioStore.getState().fetchPortfolio();

    const { summary } = usePortfolioStore.getState();
    expect(summary).not.toBeNull();
    expect(summary!.balance).toBe(1000);
    expect(summary!.total_pnl).toBe(150.5);
    expect(summary!.win_rate).toBe(0.6);
    expect(typeof summary!.balance).toBe('number');
  });

  it('fetchPortfolio sets isLoading during fetch', async () => {
    let capturedLoading = false;
    mockFetch.mockImplementationOnce(() => {
      // Capture isLoading while the fetch is "in-flight"
      capturedLoading = usePortfolioStore.getState().isLoading;
      return jsonResponse({
        id: 'p1',
        balance: '1000',
        total_deposited: '2000',
        total_pnl: '0',
        total_trades: 0,
        winning_trades: 0,
        losing_trades: 0,
        win_rate: '0',
        open_positions: 0,
        today_pnl: '0',
        today_trades: 0,
        daily_spend_used: '0',
        daily_spend_limit: '500',
      });
    });

    await usePortfolioStore.getState().fetchPortfolio();

    expect(capturedLoading).toBe(true);
    expect(usePortfolioStore.getState().isLoading).toBe(false);
  });

  it('fetchPositions calls API and parses', async () => {
    mockFetch.mockReturnValueOnce(
      jsonResponse([
        {
          id: 'pos1',
          market_id: 'm1',
          market_question: 'Will it rain?',
          market_category: 'weather',
          side: 'yes',
          shares: '50.00',
          avg_price: '0.65',
          current_price: '0.70',
          current_value: '35.00',
          unrealized_pnl: '2.50',
          cost_basis: '32.50',
          status: 'open',
          opened_at: '2024-01-01T00:00:00Z',
        },
      ])
    );

    await usePortfolioStore.getState().fetchPositions();

    const { positions } = usePortfolioStore.getState();
    expect(positions).toHaveLength(1);
    expect(positions[0].shares).toBe(50);
    expect(positions[0].avg_price).toBe(0.65);
    expect(typeof positions[0].cost_basis).toBe('number');
  });
});
