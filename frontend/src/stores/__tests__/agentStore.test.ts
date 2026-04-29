import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAgentStore } from '../agentStore';

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

beforeEach(() => {
  mockFetch.mockReset();
  useAgentStore.setState({
    status: 'idle',
    connectionState: 'disconnected',
    currentTask: null,
    uptime: 0,
    lastHeartbeat: 0,
  });
});

describe('agentStore', () => {
  it('has idle status initially', () => {
    expect(useAgentStore.getState().status).toBe('idle');
  });

  it('has disconnected connectionState initially', () => {
    expect(useAgentStore.getState().connectionState).toBe('disconnected');
  });

  it('setStatus updates status', () => {
    useAgentStore.getState().setStatus('running');
    expect(useAgentStore.getState().status).toBe('running');
  });

  it('setConnectionState updates connection state', () => {
    useAgentStore.getState().setConnectionState('connected');
    expect(useAgentStore.getState().connectionState).toBe('connected');
  });

  it('setCurrentTask updates current task', () => {
    useAgentStore.getState().setCurrentTask('Scanning markets');
    expect(useAgentStore.getState().currentTask).toBe('Scanning markets');
  });

  it('fetchStatus calls API and sets status', async () => {
    mockFetch.mockReturnValueOnce(
      jsonResponse({ status: 'running', current_task: 'Analyzing' })
    );

    await useAgentStore.getState().fetchStatus();

    const state = useAgentStore.getState();
    expect(state.status).toBe('running');
    expect(state.currentTask).toBe('Analyzing');
  });

  it('fetchStatus sets offline on error', async () => {
    mockFetch.mockReturnValueOnce(jsonResponse('Server error', false, 500));

    await useAgentStore.getState().fetchStatus();

    expect(useAgentStore.getState().status).toBe('offline');
  });

  it('startAgent calls POST and updates status', async () => {
    mockFetch.mockReturnValueOnce(
      jsonResponse({ status: 'running', current_task: null })
    );

    await useAgentStore.getState().startAgent();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/agent/start'),
      expect.objectContaining({ method: 'POST' })
    );
    expect(useAgentStore.getState().status).toBe('running');
  });

  it('pauseAgent calls POST and updates status', async () => {
    mockFetch.mockReturnValueOnce(
      jsonResponse({ status: 'paused', current_task: null })
    );

    await useAgentStore.getState().pauseAgent();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/agent/pause'),
      expect.objectContaining({ method: 'POST' })
    );
    expect(useAgentStore.getState().status).toBe('paused');
  });

  it('resumeAgent calls POST and updates status', async () => {
    mockFetch.mockReturnValueOnce(
      jsonResponse({ status: 'running', current_task: null })
    );

    await useAgentStore.getState().resumeAgent();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/agent/resume'),
      expect.objectContaining({ method: 'POST' })
    );
    expect(useAgentStore.getState().status).toBe('running');
  });
});
