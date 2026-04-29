export interface NewsItem {
  id: string;
  source: string;
  title: string;
  url: string | null;
  summary: string | null;
  relevance_score: number | null;
  credibility_score: number | null;
  sentiment_score: number | null;
  categories: string[] | null;
  fetched_at: string | null;
}
