import { dispatchServerEvent } from '@/ws/handlers';
import { useAgentStore } from '@/stores/agentStore';
import { useChatStore } from '@/stores/chatStore';
import { usePortfolioStore } from '@/stores/portfolioStore';
import { useTradeStore } from '@/stores/tradeStore';
import { useNewsStore } from '@/stores/newsStore';
import { usePolicyStore } from '@/stores/policyStore';
import { useStrategyStore } from '@/stores/strategyStore';
import { useNotificationStore } from '@/stores/notificationStore';
import { useAuthStore } from '@/stores/authStore';
import type { BackendEvent } from '@/types/ws';

// Mock the API client so store fetch methods don't actually call the network
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue([]),
    post: vi.fn().mockResolvedValue({}),
    put: vi.fn().mockResolvedValue({}),
    delete: vi.fn().mockResolvedValue({}),
  },
}));

function makeBackendEvent(type: string, data: Record<string, unknown>): BackendEvent {
  return { type, data, timestamp: new Date().toISOString() };
}

describe('dispatchServerEvent — BackendEvent dispatching', () => {
  beforeEach(() => {
    // Ensure localStorage is available (jsdom may not provide it in all setups)
    const store: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key: string) => store[key] ?? null),
      setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
      removeItem: vi.fn((key: string) => { delete store[key]; }),
      clear: vi.fn(() => { Object.keys(store).forEach((k) => delete store[k]); }),
      length: 0,
      key: vi.fn(() => null),
    });

    // Reset all Zustand stores to initial state
    useAgentStore.setState({ status: 'idle', currentTask: null });
    useChatStore.setState({ messages: [], isAgentTyping: false });
    usePortfolioStore.setState({ summary: null, positions: [], isLoading: false });
    useTradeStore.setState({ trades: [], pendingApprovals: [] });
    useNewsStore.setState({ items: [] });
    usePolicyStore.setState({ policies: [] });
    useStrategyStore.setState({ strategies: [] });
    useNotificationStore.setState({ toasts: [] });
    useAuthStore.setState({ token: null, user: null, isLoading: false, error: null });
  });

  // ---------- agent:status ----------
  it('agent:status updates agentStore status and currentTask', () => {
    dispatchServerEvent(makeBackendEvent('agent:status', {
      status: 'scanning',
      current_task: 'Looking for markets',
    }));

    expect(useAgentStore.getState().status).toBe('scanning');
    expect(useAgentStore.getState().currentTask).toBe('Looking for markets');
  });

  // ---------- agent:message (nested data.message) ----------
  it('agent:message creates chat message from nested data.message structure', () => {
    dispatchServerEvent(makeBackendEvent('agent:message', {
      message: {
        content: 'Hello from agent',
        message_type: 'text',
        data: { foo: 'bar' },
      },
    }));

    const msgs = useChatStore.getState().messages;
    expect(msgs.length).toBe(1);
    expect(msgs[0].content).toBe('Hello from agent');
    expect(msgs[0].role).toBe('agent');
    expect(msgs[0].type).toBe('text');
    expect(msgs[0].data).toEqual({ foo: 'bar' });
  });

  // ---------- agent:message (flat data, no nested message) ----------
  it('agent:message with flat data (no nested message) still works', () => {
    dispatchServerEvent(makeBackendEvent('agent:message', {
      content: 'Flat message',
      message_type: 'market_analysis',
    }));

    const msgs = useChatStore.getState().messages;
    expect(msgs.length).toBe(1);
    expect(msgs[0].content).toBe('Flat message');
    expect(msgs[0].type).toBe('market_analysis');
  });

  // ---------- agent:message extracts message_type from inner object ----------
  it('agent:message extracts message_type from inner object', () => {
    dispatchServerEvent(makeBackendEvent('agent:message', {
      message: {
        content: 'A strategy preview',
        message_type: 'strategy_preview',
      },
    }));

    const msgs = useChatStore.getState().messages;
    expect(msgs[0].type).toBe('strategy_preview');
  });

  // ---------- agent:message sets isAgentTyping to false ----------
  it('agent:message sets isAgentTyping to false', () => {
    useChatStore.setState({ isAgentTyping: true });

    dispatchServerEvent(makeBackendEvent('agent:message', {
      content: 'done typing',
    }));

    expect(useChatStore.getState().isAgentTyping).toBe(false);
  });

  // ---------- trade:executed ----------
  it('trade:executed adds trade to store and fetches portfolio', () => {
    const fetchPortfolio = vi.spyOn(usePortfolioStore.getState(), 'fetchPortfolio');
    const fetchPositions = vi.spyOn(usePortfolioStore.getState(), 'fetchPositions');

    dispatchServerEvent(makeBackendEvent('trade:executed', {
      id: 't1',
      market_id: 'm1',
      market_question: 'Will it rain?',
      action: 'buy',
      side: 'yes',
      shares: 10,
      price: 0.65,
      total_amount: 6.5,
      enforcement_result: 'approved',
      executed_at: '2025-01-01',
    }));

    const trades = useTradeStore.getState().trades;
    expect(trades.length).toBe(1);
    expect(trades[0].id).toBe('t1');
    expect(fetchPortfolio).toHaveBeenCalled();
    expect(fetchPositions).toHaveBeenCalled();

    // Should show success toast
    const toasts = useNotificationStore.getState().toasts;
    expect(toasts.length).toBeGreaterThanOrEqual(1);
    expect(toasts[0].type).toBe('success');
    expect(toasts[0].title).toBe('Trade Executed');

    fetchPortfolio.mockRestore();
    fetchPositions.mockRestore();
  });

  // ---------- trade:held ----------
  it('trade:held fetches approvals and shows notification', () => {
    const fetchApprovals = vi.spyOn(useTradeStore.getState(), 'fetchApprovals');

    dispatchServerEvent(makeBackendEvent('trade:held', {
      market_question: 'Will BTC hit 100k?',
      reason: 'Exceeds limit',
    }));

    expect(fetchApprovals).toHaveBeenCalled();

    const toasts = useNotificationStore.getState().toasts;
    expect(toasts.length).toBeGreaterThanOrEqual(1);
    expect(toasts[0].type).toBe('warning');
    expect(toasts[0].title).toBe('Trade Held');

    fetchApprovals.mockRestore();
  });

  // ---------- trade:denied ----------
  it('trade:denied shows error notification', () => {
    dispatchServerEvent(makeBackendEvent('trade:denied', {
      market_question: 'Will ETH flip BTC?',
      reason: 'Policy violation',
    }));

    const toasts = useNotificationStore.getState().toasts;
    expect(toasts.length).toBeGreaterThanOrEqual(1);
    expect(toasts[0].type).toBe('error');
    expect(toasts[0].title).toBe('Trade Denied');
  });

  // ---------- portfolio:update ----------
  it('portfolio:update fetches portfolio and positions', () => {
    const fetchPortfolio = vi.spyOn(usePortfolioStore.getState(), 'fetchPortfolio');
    const fetchPositions = vi.spyOn(usePortfolioStore.getState(), 'fetchPositions');

    dispatchServerEvent(makeBackendEvent('portfolio:update', {}));

    expect(fetchPortfolio).toHaveBeenCalled();
    expect(fetchPositions).toHaveBeenCalled();

    fetchPortfolio.mockRestore();
    fetchPositions.mockRestore();
  });

  // ---------- news:item ----------
  it('news:item adds item to news store', () => {
    dispatchServerEvent(makeBackendEvent('news:item', {
      id: 'n1',
      source: 'Reuters',
      title: 'Market rally',
      url: null,
      summary: null,
      relevance_score: 0.5,
      credibility_score: 0.9,
      sentiment_score: 0.7,
      categories: null,
      fetched_at: null,
    }));

    expect(useNewsStore.getState().items.length).toBe(1);
    expect(useNewsStore.getState().items[0].title).toBe('Market rally');
  });

  it('news:item with high relevance shows notification', () => {
    dispatchServerEvent(makeBackendEvent('news:item', {
      id: 'n2',
      source: 'AP',
      title: 'Breaking: Major event',
      url: null,
      summary: null,
      relevance_score: 0.95,
      credibility_score: 0.9,
      sentiment_score: 0.1,
      categories: null,
      fetched_at: null,
    }));

    const toasts = useNotificationStore.getState().toasts;
    expect(toasts.length).toBeGreaterThanOrEqual(1);
    expect(toasts[0].type).toBe('info');
    expect(toasts[0].title).toBe('Breaking News');
  });

  // ---------- policy:updated ----------
  it('policy:updated fetches policies', () => {
    const fetchPolicies = vi.spyOn(usePolicyStore.getState(), 'fetchPolicies');

    dispatchServerEvent(makeBackendEvent('policy:updated', {}));

    expect(fetchPolicies).toHaveBeenCalled();
    fetchPolicies.mockRestore();
  });

  // ---------- strategy:updated ----------
  it('strategy:updated fetches strategies', () => {
    const fetchStrategies = vi.spyOn(useStrategyStore.getState(), 'fetchStrategies');

    dispatchServerEvent(makeBackendEvent('strategy:updated', {}));

    expect(fetchStrategies).toHaveBeenCalled();
    fetchStrategies.mockRestore();
  });

  // ---------- onboarding:complete ----------
  it('onboarding:complete updates authStore user.onboarding_completed to true', () => {
    useAuthStore.setState({
      user: {
        id: 'u1',
        email: 'test@example.com',
        display_name: null,
        role: 'user',
        initial_balance: '1000',
        is_active: true,
        onboarding_completed: false,
        created_at: '2025-01-01',
      },
    });

    dispatchServerEvent(makeBackendEvent('onboarding:complete', {}));

    expect(useAuthStore.getState().user?.onboarding_completed).toBe(true);
  });

  it('onboarding:complete with null user does not crash', () => {
    // If user is null (e.g. race condition, logged out), the handler must not throw
    useAuthStore.setState({ user: null });

    expect(() => {
      dispatchServerEvent(makeBackendEvent('onboarding:complete', {}));
    }).not.toThrow();

    // User should still be null — no phantom user created
    expect(useAuthStore.getState().user).toBeNull();
  });

  // ---------- approval:approved ----------
  it('approval:approved removes approval and fetches trades', () => {
    useTradeStore.setState({
      pendingApprovals: [
        {
          id: 'a1',
          market_id: 'm1',
          market_question: 'Q?',
          action: 'buy',
          side: 'yes',
          shares: 5,
          price: 0.5,
          total_amount: 2.5,
          category: null,
          confidence_score: null,
          reasoning: null,
          sources: null,
          threshold_breached: null,
          status: 'pending',
          expires_at: '',
          created_at: '',
        },
      ],
    });

    const fetchTrades = vi.spyOn(useTradeStore.getState(), 'fetchTrades');
    const fetchPortfolio = vi.spyOn(usePortfolioStore.getState(), 'fetchPortfolio');

    dispatchServerEvent(makeBackendEvent('approval:approved', {
      approval_id: 'a1',
      message: 'Approved by user',
    }));

    // Approval should have been removed
    expect(useTradeStore.getState().pendingApprovals.length).toBe(0);
    expect(fetchTrades).toHaveBeenCalled();
    expect(fetchPortfolio).toHaveBeenCalled();

    // Should show success toast
    const toasts = useNotificationStore.getState().toasts;
    expect(toasts.some((t) => t.type === 'success' && t.title === 'Trade Approved')).toBe(true);

    fetchTrades.mockRestore();
    fetchPortfolio.mockRestore();
  });

  // ---------- approval:rejected ----------
  it('approval:rejected removes approval', () => {
    useTradeStore.setState({
      pendingApprovals: [
        {
          id: 'a2',
          market_id: 'm2',
          market_question: 'Q2?',
          action: 'sell',
          side: 'no',
          shares: 3,
          price: 0.4,
          total_amount: 1.2,
          category: null,
          confidence_score: null,
          reasoning: null,
          sources: null,
          threshold_breached: null,
          status: 'pending',
          expires_at: '',
          created_at: '',
        },
      ],
    });

    dispatchServerEvent(makeBackendEvent('approval:rejected', {
      approval_id: 'a2',
      message: 'Rejected by user',
    }));

    expect(useTradeStore.getState().pendingApprovals.length).toBe(0);

    const toasts = useNotificationStore.getState().toasts;
    expect(toasts.some((t) => t.type === 'error' && t.title === 'Trade Rejected')).toBe(true);
  });

  // ---------- error ----------
  it('error event shows notification and adds error message to chat', () => {
    dispatchServerEvent(makeBackendEvent('error', {
      message: 'Something went wrong',
    }));

    const toasts = useNotificationStore.getState().toasts;
    expect(toasts.length).toBeGreaterThanOrEqual(1);
    expect(toasts[0].type).toBe('error');
    expect(toasts[0].title).toBe('Error');

    const msgs = useChatStore.getState().messages;
    expect(msgs.length).toBe(1);
    expect(msgs[0].role).toBe('system');
    expect(msgs[0].type).toBe('error');
    expect(msgs[0].content).toBe('Something went wrong');
  });

  // ---------- unknown event ----------
  it('unknown event type logs warning', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    dispatchServerEvent(makeBackendEvent('totally:unknown', { foo: 'bar' }));

    expect(warnSpy).toHaveBeenCalledWith(
      '[WS] Unhandled backend event type:',
      'totally:unknown',
      { foo: 'bar' },
    );

    warnSpy.mockRestore();
  });

  // ---------- pong ----------
  it('pong event does nothing (no crash)', () => {
    expect(() => {
      dispatchServerEvent(makeBackendEvent('pong', {}));
    }).not.toThrow();

    // No toasts, no messages
    expect(useNotificationStore.getState().toasts.length).toBe(0);
    expect(useChatStore.getState().messages.length).toBe(0);
  });
});
