import { useStrategyStore } from '@/stores/strategyStore';
import { apiClient } from '@/api/client';
import type { Strategy } from '@/types/ws';

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockApiGet = vi.mocked(apiClient.get);

function makeStrategy(id: string, name = 'Default Strategy'): Strategy {
  return {
    id,
    name,
    is_active: true,
    priority: 1,
    rules: {},
    context: 'general',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };
}

describe('strategyStore', () => {
  beforeEach(() => {
    useStrategyStore.setState({ strategies: [] });
    vi.clearAllMocks();
  });

  it('initial state has empty strategies', () => {
    useStrategyStore.setState({ strategies: [] });
    expect(useStrategyStore.getState().strategies).toEqual([]);
  });

  it('setStrategies replaces', () => {
    useStrategyStore.getState().setStrategies([makeStrategy('s1')]);
    expect(useStrategyStore.getState().strategies.length).toBe(1);

    useStrategyStore.getState().setStrategies([makeStrategy('s2'), makeStrategy('s3')]);
    expect(useStrategyStore.getState().strategies.length).toBe(2);
    expect(useStrategyStore.getState().strategies[0].id).toBe('s2');
  });

  it('updateStrategy modifies matching strategy', () => {
    useStrategyStore.getState().setStrategies([
      makeStrategy('s1', 'Strategy A'),
      makeStrategy('s2', 'Strategy B'),
    ]);

    useStrategyStore.getState().updateStrategy('s1', { name: 'Updated A', priority: 5 });

    const strategies = useStrategyStore.getState().strategies;
    expect(strategies[0].name).toBe('Updated A');
    expect(strategies[0].priority).toBe(5);
    // s2 unchanged
    expect(strategies[1].name).toBe('Strategy B');
  });

  it('fetchStrategies calls API', async () => {
    const strategyData: Strategy[] = [makeStrategy('fetched-s1')];
    mockApiGet.mockResolvedValueOnce(strategyData);

    await useStrategyStore.getState().fetchStrategies();

    expect(mockApiGet).toHaveBeenCalledWith('/api/strategies');
    expect(useStrategyStore.getState().strategies).toEqual(strategyData);
  });
});
