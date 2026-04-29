import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useTradeStore } from '../tradeStore';
import type { Trade, ApprovalRequest } from '@/types/trade';

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

const sampleTrade: Trade = {
  id: 't1',
  market_id: 'm1',
  market_question: 'Will it rain?',
  market_category: 'weather',
  action: 'buy',
  side: 'yes',
  shares: 10,
  price: 0.65,
  total_amount: 6.5,
  confidence_score: 0.8,
  edge: 0.1,
  sources_count: 3,
  reasoning: 'Looks likely',
  enforcement_result: 'auto_approved',
  armoriq_plan_hash: null,
  executed_at: '2024-01-01T00:00:00Z',
};

const sampleApproval: ApprovalRequest = {
  id: 'a1',
  market_id: 'm1',
  market_question: 'Will it rain?',
  action: 'buy',
  side: 'yes',
  shares: 10,
  price: 0.65,
  total_amount: 6.5,
  category: 'weather',
  confidence_score: 0.8,
  reasoning: 'Looks likely',
  sources: null,
  threshold_breached: 'high_amount',
  status: 'pending',
  expires_at: '2024-01-02T00:00:00Z',
  created_at: '2024-01-01T00:00:00Z',
};

beforeEach(() => {
  mockFetch.mockReset();
  useTradeStore.setState({
    trades: [],
    pendingApprovals: [],
  });
});

describe('tradeStore', () => {
  it('has empty trades and pendingApprovals initially', () => {
    const state = useTradeStore.getState();
    expect(state.trades).toEqual([]);
    expect(state.pendingApprovals).toEqual([]);
  });

  it('addTrade prepends to trades array', () => {
    const t2: Trade = { ...sampleTrade, id: 't2' };
    useTradeStore.getState().addTrade(sampleTrade);
    useTradeStore.getState().addTrade(t2);
    const { trades } = useTradeStore.getState();
    expect(trades).toHaveLength(2);
    expect(trades[0].id).toBe('t2');
    expect(trades[1].id).toBe('t1');
  });

  it('updateTrade modifies a matching trade', () => {
    useTradeStore.getState().addTrade(sampleTrade);
    useTradeStore.getState().updateTrade('t1', { side: 'no' });
    expect(useTradeStore.getState().trades[0].side).toBe('no');
  });

  it('setTrades replaces all trades', () => {
    useTradeStore.getState().addTrade(sampleTrade);
    const newTrades: Trade[] = [{ ...sampleTrade, id: 'new1' }];
    useTradeStore.getState().setTrades(newTrades);
    expect(useTradeStore.getState().trades).toEqual(newTrades);
  });

  it('addApproval prepends to pendingApprovals', () => {
    const a2: ApprovalRequest = { ...sampleApproval, id: 'a2' };
    useTradeStore.getState().addApproval(sampleApproval);
    useTradeStore.getState().addApproval(a2);
    const { pendingApprovals } = useTradeStore.getState();
    expect(pendingApprovals).toHaveLength(2);
    expect(pendingApprovals[0].id).toBe('a2');
  });

  it('removeApproval filters out by id', () => {
    useTradeStore.getState().addApproval(sampleApproval);
    useTradeStore.getState().removeApproval('a1');
    expect(useTradeStore.getState().pendingApprovals).toHaveLength(0);
  });

  it('setApprovals replaces all approvals', () => {
    useTradeStore.getState().addApproval(sampleApproval);
    const newApprovals: ApprovalRequest[] = [{ ...sampleApproval, id: 'x1' }];
    useTradeStore.getState().setApprovals(newApprovals);
    expect(useTradeStore.getState().pendingApprovals).toEqual(newApprovals);
  });

  it('fetchTrades calls API and parses Decimal strings to numbers', async () => {
    mockFetch.mockReturnValueOnce(
      jsonResponse([
        {
          id: 't1',
          market_id: 'm1',
          market_question: 'Will it rain?',
          market_category: 'weather',
          action: 'buy',
          side: 'yes',
          shares: '10.00',
          price: '0.65',
          total_amount: '6.50',
          confidence_score: '0.80',
          edge: '0.10',
          sources_count: 3,
          reasoning: 'Looks likely',
          enforcement_result: 'auto_approved',
          armoriq_plan_hash: null,
          executed_at: '2024-01-01T00:00:00Z',
        },
      ])
    );

    await useTradeStore.getState().fetchTrades();

    const { trades } = useTradeStore.getState();
    expect(trades).toHaveLength(1);
    expect(trades[0].shares).toBe(10);
    expect(trades[0].price).toBe(0.65);
    expect(trades[0].total_amount).toBe(6.5);
    expect(trades[0].confidence_score).toBe(0.8);
    expect(trades[0].edge).toBe(0.1);
    expect(typeof trades[0].shares).toBe('number');
  });

  it('fetchTrades handles API error gracefully', async () => {
    mockFetch.mockReturnValueOnce(jsonResponse('Server error', false, 500));

    await useTradeStore.getState().fetchTrades();
    // Should not throw; trades remain empty
    expect(useTradeStore.getState().trades).toEqual([]);
  });

  it('fetchApprovals calls API and parses', async () => {
    mockFetch.mockReturnValueOnce(
      jsonResponse([
        {
          id: 'a1',
          market_id: 'm1',
          market_question: 'Will it rain?',
          action: 'buy',
          side: 'yes',
          shares: '10.00',
          price: '0.65',
          total_amount: '6.50',
          category: 'weather',
          confidence_score: '0.80',
          reasoning: 'Looks likely',
          sources: null,
          threshold_breached: 'high_amount',
          status: 'pending',
          expires_at: '2024-01-02T00:00:00Z',
          created_at: '2024-01-01T00:00:00Z',
        },
      ])
    );

    await useTradeStore.getState().fetchApprovals();

    const { pendingApprovals } = useTradeStore.getState();
    expect(pendingApprovals).toHaveLength(1);
    expect(pendingApprovals[0].shares).toBe(10);
    expect(typeof pendingApprovals[0].price).toBe('number');
  });

  it('approveTradeAction calls POST and removes approval', async () => {
    useTradeStore.setState({ pendingApprovals: [sampleApproval] });
    mockFetch.mockReturnValueOnce(jsonResponse({ status: 'approved' }));

    await useTradeStore.getState().approveTradeAction('a1');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/approvals/a1/approve'),
      expect.objectContaining({ method: 'POST' })
    );
    expect(useTradeStore.getState().pendingApprovals).toHaveLength(0);
  });

  it('rejectTradeAction calls POST and removes approval', async () => {
    useTradeStore.setState({ pendingApprovals: [sampleApproval] });
    mockFetch.mockReturnValueOnce(jsonResponse({ status: 'rejected' }));

    await useTradeStore.getState().rejectTradeAction('a1');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/approvals/a1/reject'),
      expect.objectContaining({ method: 'POST' })
    );
    expect(useTradeStore.getState().pendingApprovals).toHaveLength(0);
  });
});
