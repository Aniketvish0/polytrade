import React, { useState, useCallback, useRef, useEffect } from 'react';
import { ChevronRight } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { useAgentStore } from '@/stores/agentStore';
import { usePolicyStore } from '@/stores/policyStore';
import { useStrategyStore } from '@/stores/strategyStore';
import { usePortfolioStore } from '@/stores/portfolioStore';
import { formatUSD } from '@/utils/format';
import { wsClient } from '@/ws/client';

const LOCAL_COMMANDS: Record<string, string> = {
  '!/help': 'Show local commands',
  '!/clear': 'Clear the terminal',
  '!/status': 'Show agent status',
  '!/start': 'Start the trading agent',
  '!/pause': 'Pause the trading agent',
  '!/resume': 'Resume the trading agent',
  '!/policy': 'Show policies',
  '!/strategy': 'Show strategies',
  '!/portfolio': 'Show portfolio summary',
};

export function CommandInput() {
  const inputValue = useChatStore((s) => s.inputValue);
  const setInputValue = useChatStore((s) => s.setInputValue);
  const addMessage = useChatStore((s) => s.addMessage);
  const addToHistory = useChatStore((s) => s.addToHistory);
  const commandHistory = useChatStore((s) => s.commandHistory);
  const historyIndex = useChatStore((s) => s.historyIndex);
  const setHistoryIndex = useChatStore((s) => s.setHistoryIndex);
  const setIsAgentTyping = useChatStore((s) => s.setIsAgentTyping);
  const clearMessages = useChatStore((s) => s.clearMessages);

  const [suggestions, setSuggestions] = useState<{ name: string; desc: string }[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const updateSuggestions = useCallback((value: string) => {
    if (value.startsWith('!/') && value.length > 2) {
      const lower = value.toLowerCase();
      const matches = Object.entries(LOCAL_COMMANDS)
        .filter(([name]) => name.startsWith(lower))
        .map(([name, desc]) => ({ name, desc }));
      setSuggestions(matches);
      setSelectedSuggestion(0);
    } else {
      setSuggestions([]);
    }
  }, []);

  const handleLocalCommand = useCallback(
    (input: string): boolean => {
      const trimmed = input.trim().toLowerCase();
      const spaceIdx = trimmed.indexOf(' ');
      const cmd = spaceIdx === -1 ? trimmed : trimmed.slice(0, spaceIdx);

      switch (cmd) {
        case '!/help': {
          const helpText = Object.entries(LOCAL_COMMANDS)
            .map(([name, desc]) => `  ${name.padEnd(16)} ${desc}`)
            .join('\n');
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'text',
            content: `Local commands (instant, no AI):\n${helpText}\n\nEverything else goes to the AI agent — just type naturally.`,
            timestamp: Date.now(),
          });
          return true;
        }
        case '!/clear':
          clearMessages();
          return true;
        case '!/status': {
          const agentStatus = useAgentStore.getState().status;
          useAgentStore.getState().fetchStatus();
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'text',
            content: `Agent Status: ${agentStatus.toUpperCase()}\nConnection: ${useAgentStore.getState().connectionState.toUpperCase()}`,
            timestamp: Date.now(),
          });
          return true;
        }
        case '!/start':
          useAgentStore.getState().startAgent();
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'text',
            content: 'Starting agent...',
            timestamp: Date.now(),
          });
          return true;
        case '!/pause':
          useAgentStore.getState().pauseAgent();
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'text',
            content: 'Pausing agent...',
            timestamp: Date.now(),
          });
          return true;
        case '!/resume':
          useAgentStore.getState().resumeAgent();
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'text',
            content: 'Resuming agent...',
            timestamp: Date.now(),
          });
          return true;
        case '!/policy': {
          usePolicyStore.getState().fetchPolicies();
          const policies = usePolicyStore.getState().policies;
          const list = policies.length > 0
            ? policies.map((p) => `  ${p.is_active ? '[ON] ' : '[OFF]'} ${p.name}`).join('\n')
            : '  No policies configured';
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'policy_confirm',
            content: `Policies:\n${list}`,
            timestamp: Date.now(),
          });
          return true;
        }
        case '!/strategy': {
          useStrategyStore.getState().fetchStrategies();
          const strategies = useStrategyStore.getState().strategies;
          const list = strategies.length > 0
            ? strategies.map((s) => `  ${s.is_active ? '[ON] ' : '[OFF]'} ${s.name} (priority: ${s.priority})`).join('\n')
            : '  No strategies configured';
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'text',
            content: `Strategies:\n${list}`,
            timestamp: Date.now(),
          });
          return true;
        }
        case '!/portfolio': {
          usePortfolioStore.getState().fetchPortfolio();
          const summary = usePortfolioStore.getState().summary;
          if (summary) {
            addMessage({
              id: `sys-${Date.now()}`,
              role: 'system',
              type: 'text',
              content: [
                `Portfolio Summary:`,
                `  Balance:       ${formatUSD(summary.balance)}`,
                `  Total P&L:     ${formatUSD(summary.total_pnl)}`,
                `  Win Rate:      ${(summary.win_rate * 100).toFixed(1)}%`,
                `  Open Positions:${summary.open_positions}`,
                `  Today Trades:  ${summary.today_trades}`,
                `  Daily Spend:   ${formatUSD(summary.daily_spend_used)} / ${formatUSD(summary.daily_spend_limit)}`,
              ].join('\n'),
              timestamp: Date.now(),
            });
          } else {
            addMessage({
              id: `sys-${Date.now()}`,
              role: 'system',
              type: 'text',
              content: 'Portfolio data loading...',
              timestamp: Date.now(),
            });
          }
          return true;
        }
        default:
          return false;
      }
    },
    [addMessage, clearMessages]
  );

  const sendToAgent = useCallback(
    (content: string) => {
      const allMessages = useChatStore.getState().messages;
      const history = allMessages
        .filter((m) => m.role === 'user' || m.role === 'agent')
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }));
      wsClient.send({ type: 'chat:message', data: { content, history } });
      setIsAgentTyping(true);
    },
    [setIsAgentTyping]
  );

  const handleSubmit = useCallback(() => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    addToHistory(trimmed);

    addMessage({
      id: `user-${Date.now()}`,
      role: 'user',
      type: 'text',
      content: trimmed,
      timestamp: Date.now(),
    });

    if (trimmed.startsWith('!')) {
      const handled = handleLocalCommand(trimmed);
      if (!handled) {
        addMessage({
          id: `sys-${Date.now()}`,
          role: 'system',
          type: 'text',
          content: `Unknown command: ${trimmed}. Type !/help for available commands.`,
          timestamp: Date.now(),
        });
      }
    } else {
      sendToAgent(trimmed);
    }

    setInputValue('');
    setSuggestions([]);
  }, [inputValue, addToHistory, addMessage, handleLocalCommand, sendToAgent, setInputValue]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        setSuggestions([]);
        handleSubmit();
        e.preventDefault();
      } else if (e.key === 'Tab' && suggestions.length > 0) {
        e.preventDefault();
        setInputValue(suggestions[selectedSuggestion].name + ' ');
        setSuggestions([]);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (suggestions.length > 0) {
          setSelectedSuggestion((prev) =>
            prev > 0 ? prev - 1 : suggestions.length - 1
          );
        } else if (commandHistory.length > 0) {
          const newIndex = Math.min(
            historyIndex + 1,
            commandHistory.length - 1
          );
          setHistoryIndex(newIndex);
          setInputValue(commandHistory[newIndex].command);
        }
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (suggestions.length > 0) {
          setSelectedSuggestion((prev) =>
            prev < suggestions.length - 1 ? prev + 1 : 0
          );
        } else if (historyIndex > 0) {
          const newIndex = historyIndex - 1;
          setHistoryIndex(newIndex);
          setInputValue(commandHistory[newIndex].command);
        } else if (historyIndex === 0) {
          setHistoryIndex(-1);
          setInputValue('');
        }
      } else if (e.key === 'Escape') {
        setSuggestions([]);
      }
    },
    [
      suggestions,
      selectedSuggestion,
      handleSubmit,
      commandHistory,
      historyIndex,
      setInputValue,
      setHistoryIndex,
    ]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setInputValue(value);
      updateSuggestions(value);
    },
    [setInputValue, updateSuggestions]
  );

  return (
    <div className="relative shrink-0 border-t border-border bg-panel">
      {suggestions.length > 0 && (
        <div className="absolute bottom-full left-0 right-0 bg-surface border border-border border-b-0">
          {suggestions.map((suggestion, i) => (
            <div
              key={suggestion.name}
              className={`
                flex items-center gap-3 px-3 py-1 cursor-pointer
                ${i === selectedSuggestion ? 'bg-accent/10 text-accent' : 'text-secondary hover:bg-white/5'}
              `}
              onClick={() => {
                setInputValue(suggestion.name + ' ');
                setSuggestions([]);
                inputRef.current?.focus();
              }}
            >
              <span className="font-mono text-xs">{suggestion.name}</span>
              <span className="text-xxs text-muted">{suggestion.desc}</span>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 px-3 py-2">
        <ChevronRight size={14} className="text-accent shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything or use !/command for instant actions..."
          className="flex-1 bg-transparent text-sm text-primary placeholder:text-muted font-mono outline-none"
          spellCheck={false}
          autoComplete="off"
        />
      </div>
    </div>
  );
}
