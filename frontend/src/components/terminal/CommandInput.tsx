import React, { useState, useCallback, useRef, useEffect } from 'react';
import { ChevronRight } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { useAgentStore } from '@/stores/agentStore';
import { usePolicyStore } from '@/stores/policyStore';
import { useStrategyStore } from '@/stores/strategyStore';
import { usePortfolioStore } from '@/stores/portfolioStore';
import { matchCommands, parseCommand, SLASH_COMMANDS } from '@/utils/commands';
import { formatUSD, formatPercent } from '@/utils/format';
import { wsClient } from '@/ws/client';

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

  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const updateSuggestions = useCallback((value: string) => {
    if (value.startsWith('/') && value.length > 1) {
      const matches = matchCommands(value);
      setSuggestions(matches.map((m) => m.name));
      setSelectedSuggestion(0);
    } else {
      setSuggestions([]);
    }
  }, []);

  const handleLocalCommand = useCallback(
    (name: string, args: string) => {
      const agentStatus = useAgentStore.getState().status;
      const policies = usePolicyStore.getState().policies;
      const strategies = useStrategyStore.getState().strategies;
      const summary = usePortfolioStore.getState().summary;

      switch (name) {
        case '/help': {
          const helpText = SLASH_COMMANDS.map(
            (cmd) => `  ${cmd.name.padEnd(14)} ${cmd.description}`
          ).join('\n');
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'text',
            content: `Available commands:\n${helpText}`,
            timestamp: Date.now(),
          });
          return true;
        }
        case '/clear':
          clearMessages();
          return true;
        case '/status': {
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'text',
            content: `Agent Status: ${agentStatus.toUpperCase()}\nConnection: ${useAgentStore.getState().connectionState.toUpperCase()}`,
            timestamp: Date.now(),
          });
          return true;
        }
        case '/policy': {
          if (args === '' || args === 'list') {
            const list = policies
              .map(
                (p) =>
                  `  ${p.enabled ? '[ON] ' : '[OFF]'} ${p.name.padEnd(24)} ${p.description}`
              )
              .join('\n');
            addMessage({
              id: `sys-${Date.now()}`,
              role: 'system',
              type: 'policy_confirm',
              content: `Active Policies:\n${list}`,
              timestamp: Date.now(),
            });
            return true;
          }
          return false;
        }
        case '/strategy': {
          if (args === '' || args === 'list') {
            const list = strategies
              .map(
                (s) =>
                  `  ${s.enabled ? '[ON] ' : '[OFF]'} ${s.name.padEnd(24)} ${s.description}`
              )
              .join('\n');
            addMessage({
              id: `sys-${Date.now()}`,
              role: 'system',
              type: 'text',
              content: `Active Strategies:\n${list}`,
              timestamp: Date.now(),
            });
            return true;
          }
          return false;
        }
        case '/portfolio': {
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'text',
            content: [
              `Portfolio Summary:`,
              `  Total Value:  ${formatUSD(summary.totalValue)}`,
              `  Total P&L:    ${formatUSD(summary.totalPnl)} (${formatPercent(summary.totalPnlPercent)})`,
              `  Day P&L:      ${formatUSD(summary.dayPnl)} (${formatPercent(summary.dayPnlPercent)})`,
              `  Cash Balance: ${formatUSD(summary.cashBalance)}`,
              `  Positions:    ${summary.positionCount}`,
            ].join('\n'),
            timestamp: Date.now(),
          });
          return true;
        }
        case '/pause':
          wsClient.send({ type: 'pause_agent' });
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'text',
            content: 'Pause command sent to agent.',
            timestamp: Date.now(),
          });
          return true;
        case '/resume':
          wsClient.send({ type: 'resume_agent' });
          addMessage({
            id: `sys-${Date.now()}`,
            role: 'system',
            type: 'text',
            content: 'Resume command sent to agent.',
            timestamp: Date.now(),
          });
          return true;
        default:
          return false;
      }
    },
    [addMessage, clearMessages]
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

    if (trimmed.startsWith('/')) {
      const { name, args } = parseCommand(trimmed);
      const handled = handleLocalCommand(name, args);
      if (!handled) {
        wsClient.send({ type: 'chat:message', data: { content: `${name} ${args}`.trim() } });
        setIsAgentTyping(true);
      }
    } else {
      wsClient.send({ type: 'chat:message', data: { content: trimmed } });
      setIsAgentTyping(true);
    }

    setInputValue('');
    setSuggestions([]);
  }, [inputValue, addToHistory, addMessage, handleLocalCommand, setInputValue, setIsAgentTyping]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        if (suggestions.length > 0) {
          setInputValue(suggestions[selectedSuggestion] + ' ');
          setSuggestions([]);
        } else {
          handleSubmit();
        }
        e.preventDefault();
      } else if (e.key === 'Tab' && suggestions.length > 0) {
        e.preventDefault();
        setInputValue(suggestions[selectedSuggestion] + ' ');
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
          {suggestions.map((suggestion, i) => {
            const cmd = SLASH_COMMANDS.find((c) => c.name === suggestion);
            return (
              <div
                key={suggestion}
                className={`
                  flex items-center gap-3 px-3 py-1 cursor-pointer
                  ${i === selectedSuggestion ? 'bg-accent/10 text-accent' : 'text-secondary hover:bg-white/5'}
                `}
                onClick={() => {
                  setInputValue(suggestion + ' ');
                  setSuggestions([]);
                  inputRef.current?.focus();
                }}
              >
                <span className="font-mono text-xs">{suggestion}</span>
                {cmd && (
                  <span className="text-xxs text-muted">{cmd.description}</span>
                )}
              </div>
            );
          })}
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
          placeholder="Type a message or /command..."
          className="flex-1 bg-transparent text-sm text-primary placeholder:text-muted font-mono outline-none"
          spellCheck={false}
          autoComplete="off"
        />
      </div>
    </div>
  );
}
