import type { ChatMessage } from '@/types/chat';
import ReactMarkdown from 'react-markdown';
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
      case 'policy_preview':
        return (
          <div className="px-2 py-1 bg-surface border border-border">
            <span className="text-xs text-held font-mono">POLICY</span>
            <span className="text-xs text-secondary ml-2 whitespace-pre-wrap">{message.content}</span>
          </div>
        );
      case 'strategy_preview':
        return (
          <div className="px-2 py-1 bg-surface border border-border">
            <span className="text-xs text-accent font-mono">STRATEGY</span>
            <span className="text-xs text-secondary ml-2 whitespace-pre-wrap">{message.content}</span>
          </div>
        );
      case 'market_analysis':
        return (
          <div className="px-2 py-1 bg-surface border border-border">
            <span className="text-xs text-approved font-mono">ANALYSIS</span>
            <span className="text-xs text-secondary ml-2 whitespace-pre-wrap">{message.content}</span>
          </div>
        );
      case 'onboarding_step': {
        const options = (message.data?.options as string[]) ?? [];
        return (
          <div className="space-y-1.5">
            <span className="text-xs text-primary whitespace-pre-wrap">
              {message.content}
            </span>
            {options.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1">
                {options.map((opt) => (
                  <span
                    key={opt}
                    className="px-2 py-0.5 text-xxs font-mono bg-surface border border-border text-secondary rounded cursor-pointer hover:border-accent hover:text-accent transition-colors"
                    onClick={() => {
                      const input = document.querySelector<HTMLInputElement>('input[type="text"]');
                      if (input) {
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                        nativeInputValueSetter?.call(input, opt);
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.focus();
                      }
                    }}
                  >
                    {opt}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      }
      case 'text':
      default:
        if (message.role === 'agent' && /[*_`#\[]/.test(message.content)) {
          return (
            <div className="text-xs text-primary prose prose-invert prose-xs max-w-none [&_p]:my-0.5 [&_ul]:my-0.5 [&_ol]:my-0.5 [&_li]:my-0 [&_strong]:text-accent [&_code]:text-accent [&_code]:bg-surface [&_code]:px-1 [&_code]:py-px [&_code]:text-xxs [&_h1]:text-sm [&_h2]:text-xs [&_h3]:text-xs [&_a]:text-accent">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          );
        }
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
