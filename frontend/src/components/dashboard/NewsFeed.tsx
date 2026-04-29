import { Newspaper } from 'lucide-react';
import { useNewsStore } from '@/stores/newsStore';
import { PanelHeader } from '@/components/shared/PanelHeader';
import { formatRelativeTime } from '@/utils/format';

export function NewsFeed() {
  const items = useNewsStore((s) => s.items);

  return (
    <div className="flex flex-col h-full">
      <PanelHeader
        label="News Feed"
        icon={<Newspaper size={11} />}
      />

      <div className="flex-1 overflow-y-auto min-h-0">
        {items.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-xs text-muted">No news items</span>
          </div>
        ) : (
          <div className="divide-y divide-border/50">
            {items.map((item) => {
              const relevance = item.relevance_score ?? 0;
              const sentiment = item.sentiment_score ?? 0;
              const sentimentLabel = sentiment > 0.2 ? 'positive' : sentiment < -0.2 ? 'negative' : 'neutral';
              const sentimentColor = sentimentLabel === 'positive' ? 'text-approved' : sentimentLabel === 'negative' ? 'text-denied' : 'text-muted';

              return (
                <div
                  key={item.id}
                  className="flex items-start gap-2 px-3 py-1.5 hover:bg-white/[0.02] transition-colors"
                >
                  {/* Relevance dots */}
                  <div className="flex gap-px mt-1.5 shrink-0">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div
                        key={i}
                        className={`w-1 h-1 ${
                          i <= Math.round(relevance * 5)
                            ? 'bg-accent'
                            : 'bg-border'
                        }`}
                      />
                    ))}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-primary leading-snug truncate">
                      {item.url ? (
                        <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:text-accent">
                          {item.title}
                        </a>
                      ) : (
                        item.title
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-px">
                      <span className="text-xxs text-muted">{item.source}</span>
                      <span className={`text-xxs font-mono ${sentimentColor}`}>
                        {sentimentLabel === 'positive'
                          ? '+'
                          : sentimentLabel === 'negative'
                            ? '-'
                            : '~'}
                      </span>
                    </div>
                  </div>

                  <span className="text-xxs text-muted font-mono shrink-0">
                    {item.fetched_at ? formatRelativeTime(new Date(item.fetched_at).getTime()) : ''}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
