import { MessageList } from '@/components/terminal/MessageList';
import { CommandInput } from '@/components/terminal/CommandInput';
import { useChatStore } from '@/stores/chatStore';
import { useAgentStore } from '@/stores/agentStore';
import { wsClient } from '@/ws/client';
import { useEffect, useRef } from 'react';

export function OnboardingShell() {
  const messages = useChatStore((s) => s.messages);
  const connectionState = useAgentStore((s) => s.connectionState);
  const triggeredRef = useRef(false);

  useEffect(() => {
    useChatStore.setState({
      messages: [
        {
          id: 'onboard-welcome',
          role: 'system',
          type: 'text',
          content: 'Welcome to POLYTRADE. Setting up your trading agent...',
          timestamp: Date.now(),
        },
      ],
    });
  }, []);

  useEffect(() => {
    if (triggeredRef.current) return;
    if (connectionState !== 'connected') return;

    triggeredRef.current = true;
    wsClient.send({ type: 'chat:message', data: { content: '__onboarding_start__' } });
    useChatStore.getState().setIsAgentTyping(true);
  }, [connectionState]);

  const latestStep = (() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.type === 'onboarding_step' && m.data?.step) {
        return m.data.step as number;
      }
    }
    return 0;
  })();

  const totalSteps = 3;
  const progressPct = Math.min((latestStep / totalSteps) * 100, 100);

  return (
    <div className="flex flex-col h-screen w-screen bg-base overflow-hidden">
      <header className="flex items-center justify-between h-8 px-3 bg-panel border-b border-border shrink-0 select-none">
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm font-bold tracking-widest text-primary">
            POLYTRADE
          </span>
          <span className="text-xxs text-muted font-mono">SETUP</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-xxs text-secondary">
            Step {Math.min(latestStep, totalSteps)}/{totalSteps}
          </span>
          <div className="w-24 h-1 bg-surface rounded overflow-hidden">
            <div
              className="h-full bg-accent transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </header>

      <div className="flex flex-col flex-1 min-h-0 max-w-3xl mx-auto w-full">
        <MessageList />
        <CommandInput />
      </div>
    </div>
  );
}
