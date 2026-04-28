import type { ChatMessage } from '@/types/chat';
import type { NewsItem } from '@/types/news';
import { Newspaper, ExternalLink } from 'lucide-react';

interface NewsCardProps {
  message: ChatMessage;
}

const sentimentColors = {
  positive: 'text-approved',
  negative: 'text-denied',
  neutral: 'text-secondary',
};

export function NewsCard({ message }: NewsCardProps) {
  const newsItem = message.data as unknown as NewsItem | undefined;

  if (!newsItem) {
    return (
      <div className="px-2 py-1 bg-surface border border-border">
        <span className="text-xs text-secondary">{message.content}</span>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border p-2 space-y-1 max-w-md">
      <div className="flex items-center gap-1.5">
        <Newspaper size={11} className="text-accent" />
        <span className="font-mono text-xxs text-accent">NEWS</span>
        <span className="text-xxs text-muted">{newsItem.source}</span>
      </div>

      <div className="text-xs text-primary font-medium leading-snug">
        {newsItem.headline}
      </div>

      <div className="text-xxs text-secondary leading-relaxed">
        {newsItem.summary}
      </div>

      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center gap-2">
          <span className={`text-xxs font-mono ${sentimentColors[newsItem.sentiment]}`}>
            {newsItem.sentiment.toUpperCase()}
          </span>
          <div className="flex items-center gap-0.5">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className={`w-1 h-1 ${
                  i <= Math.round(newsItem.relevance * 5)
                    ? 'bg-accent'
                    : 'bg-border'
                }`}
              />
            ))}
          </div>
        </div>

        {newsItem.url && (
          <a
            href={newsItem.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xxs text-muted hover:text-accent flex items-center gap-0.5"
          >
            <ExternalLink size={9} />
            SOURCE
          </a>
        )}
      </div>

      {newsItem.relatedMarkets.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {newsItem.relatedMarkets.map((market) => (
            <span
              key={market}
              className="font-mono text-xxs text-muted bg-base px-1 py-px"
            >
              {market}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
