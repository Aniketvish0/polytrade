import { Newspaper } from 'lucide-react';
import { useNewsStore } from '@/stores/newsStore';
import { PanelHeader } from '@/components/shared/PanelHeader';
import { formatRelativeTime } from '@/utils/format';

const sentimentColors = {
  positive: 'text-approved',
  negative: 'text-denied',
  neutral: 'text-muted',
};

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
            {items.map((item) => (
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
                        i <= Math.round(item.relevance * 5)
                          ? 'bg-accent'
                          : 'bg-border'
                      }`}
                    />
                  ))}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="text-xs text-primary leading-snug truncate">
                    {item.headline}
                  </div>
                  <div className="flex items-center gap-2 mt-px">
                    <span className="text-xxs text-muted">{item.source}</span>
                    <span className={`text-xxs font-mono ${sentimentColors[item.sentiment]}`}>
                      {item.sentiment === 'positive'
                        ? '+'
                        : item.sentiment === 'negative'
                          ? '-'
                          : '~'}
                    </span>
                  </div>
                </div>

                <span className="text-xxs text-muted font-mono shrink-0">
                  {formatRelativeTime(item.timestamp)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
