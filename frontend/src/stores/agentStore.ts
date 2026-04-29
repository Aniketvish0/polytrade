import { create } from 'zustand';
import type { AgentStatus, ConnectionState } from '@/types/agent';
import { apiClient } from '@/api/client';

interface AgentStore {
  status: AgentStatus;
  connectionState: ConnectionState;
  currentTask: string | null;
  uptime: number;
  lastHeartbeat: number;

  setStatus: (status: AgentStatus) => void;
  setConnectionState: (state: ConnectionState) => void;
  setCurrentTask: (task: string | null) => void;
  setHeartbeat: (timestamp: number) => void;
  fetchStatus: () => Promise<void>;
  startAgent: () => Promise<void>;
  pauseAgent: () => Promise<void>;
  resumeAgent: () => Promise<void>;
}

interface AgentStatusResponse {
  status: string;
  current_task: string | null;
}

export const useAgentStore = create<AgentStore>((set) => ({
  status: 'idle',
  connectionState: 'disconnected',
  currentTask: null,
  uptime: 0,
  lastHeartbeat: 0,

  setStatus: (status) => set({ status }),
  setConnectionState: (state) => set({ connectionState: state }),
  setCurrentTask: (task) => set({ currentTask: task }),
  setHeartbeat: (timestamp) => set({ lastHeartbeat: timestamp }),

  fetchStatus: async () => {
    try {
      const data = await apiClient.get<AgentStatusResponse>('/api/agent/status');
      set({ status: data.status as AgentStatus, currentTask: data.current_task });
    } catch {
      set({ status: 'offline' });
    }
  },

  startAgent: async () => {
    try {
      const data = await apiClient.post<AgentStatusResponse>('/api/agent/start');
      set({ status: data.status as AgentStatus });
    } catch (err) {
      console.error('Failed to start agent:', err);
    }
  },

  pauseAgent: async () => {
    try {
      const data = await apiClient.post<AgentStatusResponse>('/api/agent/pause');
      set({ status: data.status as AgentStatus });
    } catch (err) {
      console.error('Failed to pause agent:', err);
    }
  },

  resumeAgent: async () => {
    try {
      const data = await apiClient.post<AgentStatusResponse>('/api/agent/resume');
      set({ status: data.status as AgentStatus });
    } catch (err) {
      console.error('Failed to resume agent:', err);
    }
  },
}));
