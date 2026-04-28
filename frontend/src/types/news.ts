export interface NewsItem {
  id: string;
  headline: string;
  summary: string;
  source: string;
  url?: string;
  relevance: number;
  relatedMarkets: string[];
  sentiment: 'positive' | 'negative' | 'neutral';
  timestamp: number;
}
