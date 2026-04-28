import { create } from 'zustand';
import type { AgentStatus, ConnectionState } from '@/types/agent';

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
}));
