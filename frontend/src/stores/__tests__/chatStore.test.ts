import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '../chatStore';
import type { ChatMessage } from '@/types/chat';

// Reset the store before each test
beforeEach(() => {
  useChatStore.setState({
    messages: [
      {
        id: 'welcome-1',
        role: 'system',
        type: 'text',
        content:
          'POLYTRADE Terminal v0.1.0 initialized. Type /help for available commands.',
        timestamp: Date.now(),
      },
    ],
    commandHistory: [],
    historyIndex: -1,
    inputValue: '',
    isAgentTyping: false,
  });
});

describe('chatStore', () => {
  it('has a welcome message in initial state', () => {
    const { messages } = useChatStore.getState();
    expect(messages).toHaveLength(1);
    expect(messages[0].role).toBe('system');
    expect(messages[0].content).toContain('POLYTRADE Terminal');
  });

  it('addMessage appends a message', () => {
    const msg: ChatMessage = {
      id: 'msg-1',
      role: 'user',
      type: 'text',
      content: 'hello',
      timestamp: Date.now(),
    };
    useChatStore.getState().addMessage(msg);
    const { messages } = useChatStore.getState();
    expect(messages).toHaveLength(2);
    expect(messages[1]).toEqual(msg);
  });

  it('setInputValue updates the input', () => {
    useChatStore.getState().setInputValue('test input');
    expect(useChatStore.getState().inputValue).toBe('test input');
  });

  it('setIsAgentTyping toggles typing state', () => {
    expect(useChatStore.getState().isAgentTyping).toBe(false);
    useChatStore.getState().setIsAgentTyping(true);
    expect(useChatStore.getState().isAgentTyping).toBe(true);
    useChatStore.getState().setIsAgentTyping(false);
    expect(useChatStore.getState().isAgentTyping).toBe(false);
  });

  it('addToHistory adds command and resets historyIndex to -1', () => {
    useChatStore.getState().setHistoryIndex(2);
    useChatStore.getState().addToHistory('/help');
    const state = useChatStore.getState();
    expect(state.commandHistory).toHaveLength(1);
    expect(state.commandHistory[0].command).toBe('/help');
    expect(state.historyIndex).toBe(-1);
  });

  it('setHistoryIndex updates the index', () => {
    useChatStore.getState().setHistoryIndex(3);
    expect(useChatStore.getState().historyIndex).toBe(3);
  });

  it('clearMessages resets to a "Terminal cleared." message', () => {
    const msg: ChatMessage = {
      id: 'msg-2',
      role: 'user',
      type: 'text',
      content: 'something',
      timestamp: Date.now(),
    };
    useChatStore.getState().addMessage(msg);
    useChatStore.getState().clearMessages();
    const { messages } = useChatStore.getState();
    expect(messages).toHaveLength(1);
    expect(messages[0].content).toBe('Terminal cleared.');
    expect(messages[0].role).toBe('system');
  });
});
