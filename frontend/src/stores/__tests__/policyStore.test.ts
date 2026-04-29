import { usePolicyStore } from '@/stores/policyStore';
import { apiClient } from '@/api/client';
import type { Policy } from '@/types/ws';

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockApiGet = vi.mocked(apiClient.get);

function makePolicy(id: string, name = 'Default Policy'): Policy {
  return {
    id,
    name,
    is_active: true,
    global_rules: {},
    category_rules: {},
    confidence_rules: {},
    risk_rules: {},
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };
}

describe('policyStore', () => {
  beforeEach(() => {
    usePolicyStore.setState({ policies: [] });
    vi.clearAllMocks();
  });

  it('initial state has empty policies', () => {
    usePolicyStore.setState({ policies: [] });
    expect(usePolicyStore.getState().policies).toEqual([]);
  });

  it('setPolicies replaces', () => {
    usePolicyStore.getState().setPolicies([makePolicy('p1')]);
    expect(usePolicyStore.getState().policies.length).toBe(1);

    usePolicyStore.getState().setPolicies([makePolicy('p2'), makePolicy('p3')]);
    expect(usePolicyStore.getState().policies.length).toBe(2);
    expect(usePolicyStore.getState().policies[0].id).toBe('p2');
  });

  it('updatePolicy modifies matching policy', () => {
    usePolicyStore.getState().setPolicies([
      makePolicy('p1', 'Policy A'),
      makePolicy('p2', 'Policy B'),
    ]);

    usePolicyStore.getState().updatePolicy('p1', { name: 'Updated A', is_active: false });

    const policies = usePolicyStore.getState().policies;
    expect(policies[0].name).toBe('Updated A');
    expect(policies[0].is_active).toBe(false);
    // p2 unchanged
    expect(policies[1].name).toBe('Policy B');
  });

  it('fetchPolicies calls API', async () => {
    const policyData: Policy[] = [makePolicy('fetched-p1')];
    mockApiGet.mockResolvedValueOnce(policyData);

    await usePolicyStore.getState().fetchPolicies();

    expect(mockApiGet).toHaveBeenCalledWith('/api/policies');
    expect(usePolicyStore.getState().policies).toEqual(policyData);
  });
});
