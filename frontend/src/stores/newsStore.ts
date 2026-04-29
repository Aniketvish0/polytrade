import { create } from 'zustand';
import type { NewsItem } from '@/types/news';
import { apiClient } from '@/api/client';

interface NewsStore {
  items: NewsItem[];

  addItem: (item: NewsItem) => void;
  setItems: (items: NewsItem[]) => void;
  clearItems: () => void;
  fetchNews: () => Promise<void>;
}

export const useNewsStore = create<NewsStore>((set) => ({
  items: [],

  addItem: (item) =>
    set((state) => ({ items: [item, ...state.items].slice(0, 50) })),

  setItems: (items) => set({ items }),

  clearItems: () => set({ items: [] }),

  fetchNews: async () => {
    try {
      const data = await apiClient.get<NewsItem[]>('/api/news');
      set({ items: data });
    } catch {
      // no news yet
    }
  },
}));
