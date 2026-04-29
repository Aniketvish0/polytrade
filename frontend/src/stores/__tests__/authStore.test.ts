import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '../authStore';
import type { AuthUser } from '../authStore';

// ---------- mock fetch globally ----------
const mockFetch = vi.fn();
global.fetch = mockFetch;

function jsonResponse(body: unknown, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(typeof body === 'string' ? body : JSON.stringify(body)),
  });
}

const sampleUser: AuthUser = {
  id: 'u1',
  email: 'test@example.com',
  display_name: 'Test User',
  role: 'user',
  initial_balance: '1000.00',
  is_active: true,
  onboarding_completed: false,
  created_at: '2024-01-01T00:00:00Z',
};

const sampleAuthResponse = {
  access_token: 'tok_abc123',
  token_type: 'bearer',
  user: sampleUser,
};

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((_index: number) => null),
  };
})();

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

beforeEach(() => {
  mockFetch.mockReset();
  localStorageMock.clear();
  (localStorageMock.getItem as ReturnType<typeof vi.fn>).mockClear();
  (localStorageMock.setItem as ReturnType<typeof vi.fn>).mockClear();
  (localStorageMock.removeItem as ReturnType<typeof vi.fn>).mockClear();
  useAuthStore.setState({
    token: null,
    user: null,
    isLoading: false,
    error: null,
  });
});

describe('authStore', () => {
  it('initial state loads from localStorage', () => {
    // The store's initial state calls loadToken() and loadUser() which
    // read from localStorage. After our reset, both should be null.
    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('login makes POST to /api/auth/login', async () => {
    mockFetch.mockReturnValueOnce(jsonResponse(sampleAuthResponse));

    await useAuthStore.getState().login('test@example.com', 'password123');

    expect(mockFetch).toHaveBeenCalledWith('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'password123',
      }),
    });
  });

  it('login stores token and user in localStorage', async () => {
    mockFetch.mockReturnValueOnce(jsonResponse(sampleAuthResponse));

    await useAuthStore.getState().login('test@example.com', 'password123');

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'polytrade_auth_token',
      'tok_abc123'
    );
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'polytrade_auth_user',
      JSON.stringify(sampleUser)
    );
    const state = useAuthStore.getState();
    expect(state.token).toBe('tok_abc123');
    expect(state.user).toEqual(sampleUser);
  });

  it('login sets error on failure', async () => {
    mockFetch.mockReturnValueOnce(jsonResponse('Invalid credentials', false, 401));

    await useAuthStore.getState().login('bad@example.com', 'wrong');

    const state = useAuthStore.getState();
    expect(state.error).toBe('Invalid credentials');
    expect(state.token).toBeNull();
    expect(state.isLoading).toBe(false);
  });

  it('register makes POST to /api/auth/register', async () => {
    mockFetch.mockReturnValueOnce(jsonResponse(sampleAuthResponse));

    await useAuthStore.getState().register('new@example.com', 'password123');

    expect(mockFetch).toHaveBeenCalledWith('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'new@example.com',
        password: 'password123',
      }),
    });
    const state = useAuthStore.getState();
    expect(state.token).toBe('tok_abc123');
    expect(state.user).toEqual(sampleUser);
  });

  it('logout clears token, user, and localStorage', () => {
    useAuthStore.setState({
      token: 'tok_abc123',
      user: sampleUser,
    });

    useAuthStore.getState().logout();

    expect(localStorageMock.removeItem).toHaveBeenCalledWith(
      'polytrade_auth_token'
    );
    expect(localStorageMock.removeItem).toHaveBeenCalledWith(
      'polytrade_auth_user'
    );
    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
  });

  it('clearError clears the error', () => {
    useAuthStore.setState({ error: 'Something went wrong' });
    useAuthStore.getState().clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });

  it('setUser updates user and localStorage', () => {
    useAuthStore.getState().setUser(sampleUser);

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'polytrade_auth_user',
      JSON.stringify(sampleUser)
    );
    expect(useAuthStore.getState().user).toEqual(sampleUser);
  });

  it('onboarding_completed field exists on user type', () => {
    useAuthStore.getState().setUser(sampleUser);
    const user = useAuthStore.getState().user;
    expect(user).not.toBeNull();
    expect('onboarding_completed' in user!).toBe(true);
    expect(user!.onboarding_completed).toBe(false);
  });

  // ============================================================
  // QA-perspective tests: stale localStorage & edge cases
  // These tests target the bug where existing users (whose
  // localStorage was saved before onboarding_completed existed)
  // were incorrectly routed into onboarding.
  // ============================================================

  it('defaults onboarding_completed to true for stale localStorage user (pre-onboarding schema)', async () => {
    // Simulate a user object saved BEFORE onboarding_completed field existed
    const staleUser = {
      id: 'u1',
      email: 'old@example.com',
      display_name: 'Old User',
      role: 'user',
      initial_balance: '1000.00',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      // NOTE: no onboarding_completed field at all
    };
    localStorage.setItem('polytrade_auth_user', JSON.stringify(staleUser));

    // Re-import the module so loadUser() runs against the stale localStorage
    vi.resetModules();
    const { useAuthStore: freshStore } = await import('../authStore');
    const user = freshStore.getState().user;

    expect(user).not.toBeNull();
    expect(user!.onboarding_completed).toBe(true);
  });

  it('keeps onboarding_completed=false when explicitly stored as false', async () => {
    // A new user mid-onboarding — must NOT be defaulted to true
    const midOnboardingUser = {
      id: 'u2',
      email: 'new@example.com',
      display_name: 'New User',
      role: 'user',
      initial_balance: '500.00',
      is_active: true,
      onboarding_completed: false,
      created_at: '2025-06-01T00:00:00Z',
    };
    localStorage.setItem('polytrade_auth_user', JSON.stringify(midOnboardingUser));

    vi.resetModules();
    const { useAuthStore: freshStore } = await import('../authStore');
    const user = freshStore.getState().user;

    expect(user).not.toBeNull();
    expect(user!.onboarding_completed).toBe(false);
  });

  it('keeps onboarding_completed=true when explicitly stored as true', async () => {
    const completedUser = {
      id: 'u3',
      email: 'done@example.com',
      display_name: 'Done User',
      role: 'user',
      initial_balance: '2000.00',
      is_active: true,
      onboarding_completed: true,
      created_at: '2025-03-15T00:00:00Z',
    };
    localStorage.setItem('polytrade_auth_user', JSON.stringify(completedUser));

    vi.resetModules();
    const { useAuthStore: freshStore } = await import('../authStore');
    const user = freshStore.getState().user;

    expect(user).not.toBeNull();
    expect(user!.onboarding_completed).toBe(true);
  });

  it('returns null for corrupted localStorage JSON without throwing', async () => {
    localStorage.setItem('polytrade_auth_user', '{not valid json!!!');

    vi.resetModules();
    const { useAuthStore: freshStore } = await import('../authStore');
    const user = freshStore.getState().user;

    expect(user).toBeNull();
  });

  it('returns null when localStorage has no user key at all', async () => {
    // localStorage is already cleared by beforeEach — no user key present

    vi.resetModules();
    const { useAuthStore: freshStore } = await import('../authStore');
    const user = freshStore.getState().user;

    expect(user).toBeNull();
  });

  it('setUser persists onboarding_completed accurately to localStorage', () => {
    const userWithOnboarding: AuthUser = {
      ...sampleUser,
      onboarding_completed: true,
    };

    useAuthStore.getState().setUser(userWithOnboarding);

    const stored = JSON.parse(localStorage.getItem('polytrade_auth_user')!);
    expect(stored.onboarding_completed).toBe(true);
  });

  it('login response with onboarding_completed=false is stored correctly (not defaulted)', async () => {
    const loginResponse = {
      access_token: 'tok_new_user',
      token_type: 'bearer',
      user: {
        ...sampleUser,
        onboarding_completed: false,
      },
    };
    mockFetch.mockReturnValueOnce(jsonResponse(loginResponse));

    await useAuthStore.getState().login('new@example.com', 'password123');

    const state = useAuthStore.getState();
    expect(state.user).not.toBeNull();
    expect(state.user!.onboarding_completed).toBe(false);

    // Also verify it was persisted as false, not defaulted to true
    const stored = JSON.parse(localStorage.getItem('polytrade_auth_user')!);
    expect(stored.onboarding_completed).toBe(false);
  });
});
