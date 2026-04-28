import { create } from 'zustand';
import type { NewsItem } from '@/types/news';

interface NewsStore {
  items: NewsItem[];

  addItem: (item: NewsItem) => void;
  setItems: (items: NewsItem[]) => void;
  clearItems: () => void;
}

const mockNews: NewsItem[] = [
  {
    id: 'news-1',
    headline: 'Federal Reserve signals potential rate adjustment in upcoming meeting',
    summary: 'Fed officials hint at reconsidering current monetary policy stance amid inflation data.',
    source: 'Reuters',
    relevance: 0.95,
    relatedMarkets: ['Fed Rate Cut March'],
    sentiment: 'positive',
    timestamp: Date.now() - 120000,
  },
  {
    id: 'news-2',
    headline: 'New polling data shifts election prediction markets',
    summary: 'Latest nationwide polls show tightening race affecting prediction market odds.',
    source: 'AP News',
    relevance: 0.88,
    relatedMarkets: ['Presidential Election 2024'],
    sentiment: 'neutral',
    timestamp: Date.now() - 240000,
  },
  {
    id: 'news-3',
    headline: 'Bitcoin ETF inflows hit record levels for third consecutive week',
    summary: 'Institutional demand for Bitcoin exposure continues to accelerate.',
    source: 'Bloomberg',
    relevance: 0.72,
    relatedMarkets: ['BTC > 100k by EOY'],
    sentiment: 'positive',
    timestamp: Date.now() - 500000,
  },
  {
    id: 'news-4',
    headline: 'Supreme Court to hear key regulatory case next term',
    summary: 'Justices agree to review federal agency authority in landmark case.',
    source: 'WSJ',
    relevance: 0.65,
    relatedMarkets: ['Supreme Court Ruling'],
    sentiment: 'neutral',
    timestamp: Date.now() - 800000,
  },
];

export const useNewsStore = create<NewsStore>((set) => ({
  items: mockNews,

  addItem: (item) =>
    set((state) => ({ items: [item, ...state.items].slice(0, 50) })),

  setItems: (items) => set({ items }),

  clearItems: () => set({ items: [] }),
}));
