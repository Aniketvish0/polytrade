import { useChatStore } from '@/stores/chatStore';
import { MessageBubble } from './MessageBubble';
import { useAutoScroll } from '@/hooks/useAutoScroll';

export function MessageList() {
  const messages = useChatStore((s) => s.messages);
  const isAgentTyping = useChatStore((s) => s.isAgentTyping);
  const { containerRef } = useAutoScroll([messages.length, isAgentTyping]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto px-3 py-2 space-y-1 min-h-0"
    >
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {isAgentTyping && (
        <div className="flex items-center gap-2 px-2 py-1">
          <span className="text-xxs text-accent font-mono">AGENT</span>
          <span className="text-xs text-secondary typing-indicator">
            processing
          </span>
        </div>
      )}
    </div>
  );
}
