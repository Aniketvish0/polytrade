import type { ChatMessage } from '@/types/chat';
import { TradeProposalCard } from './cards/TradeProposalCard';
import { NewsCard } from './cards/NewsCard';
import { ErrorCard } from './cards/ErrorCard';
import { formatTimestamp } from '@/utils/format';

interface MessageBubbleProps {
  message: ChatMessage;
}

const roleColors: Record<string, string> = {
  user: 'text-accent',
  agent: 'text-approved',
  system: 'text-muted',
};

const roleLabels: Record<string, string> = {
  user: 'YOU',
  agent: 'AGENT',
  system: 'SYS',
};

export function MessageBubble({ message }: MessageBubbleProps) {
  const renderContent = () => {
    switch (message.type) {
      case 'trade_proposal':
      case 'approval_request':
        return <TradeProposalCard message={message} />;
      case 'news_summary':
        return <NewsCard message={message} />;
      case 'error':
        return <ErrorCard message={message} />;
      case 'policy_confirm':
        return (
          <div className="px-2 py-1 bg-surface border border-border">
            <span className="text-xs text-held font-mono">POLICY</span>
            <span className="text-xs text-secondary ml-2">{message.content}</span>
          </div>
        );
      case 'text':
      default:
        return (
          <span className="text-xs text-primary whitespace-pre-wrap">
            {message.content}
          </span>
        );
    }
  };

  return (
    <div className="group flex flex-col gap-0.5 py-0.5">
      <div className="flex items-baseline gap-2">
        <span className={`font-mono text-xxs font-semibold ${roleColors[message.role]}`}>
          {roleLabels[message.role]}
        </span>
        <span className="font-mono text-xxs text-muted">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>
      <div className="pl-0">{renderContent()}</div>
    </div>
  );
}
