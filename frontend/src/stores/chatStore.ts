import { create } from 'zustand';
import type { ChatMessage, CommandHistoryEntry } from '@/types/chat';

interface ChatStore {
  messages: ChatMessage[];
  commandHistory: CommandHistoryEntry[];
  historyIndex: number;
  inputValue: string;
  isAgentTyping: boolean;

  addMessage: (message: ChatMessage) => void;
  setInputValue: (value: string) => void;
  setIsAgentTyping: (typing: boolean) => void;
  addToHistory: (command: string) => void;
  setHistoryIndex: (index: number) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [
    {
      id: 'welcome-1',
      role: 'system',
      type: 'text',
      content: 'POLYTRADE Terminal v0.1.0 initialized. Type /help for available commands.',
      timestamp: Date.now(),
    },
  ],
  commandHistory: [],
  historyIndex: -1,
  inputValue: '',
  isAgentTyping: false,

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  setInputValue: (value) => set({ inputValue: value }),

  setIsAgentTyping: (typing) => set({ isAgentTyping: typing }),

  addToHistory: (command) =>
    set((state) => ({
      commandHistory: [
        { command, timestamp: Date.now() },
        ...state.commandHistory,
      ],
      historyIndex: -1,
    })),

  setHistoryIndex: (index) => set({ historyIndex: index }),

  clearMessages: () =>
    set({
      messages: [
        {
          id: `clear-${Date.now()}`,
          role: 'system',
          type: 'text',
          content: 'Terminal cleared.',
          timestamp: Date.now(),
        },
      ],
    }),
}));
