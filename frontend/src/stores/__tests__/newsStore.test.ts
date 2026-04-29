import { useNewsStore } from '@/stores/newsStore';
import { apiClient } from '@/api/client';
import type { NewsItem } from '@/types/news';

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockApiGet = vi.mocked(apiClient.get);

function makeItem(id: string, title = 'News'): NewsItem {
  return {
    id,
    source: 'test',
    title,
    url: null,
    summary: null,
    relevance_score: 0.5,
    credibility_score: 0.8,
    sentiment_score: 0.0,
    categories: null,
    fetched_at: null,
  };
}

describe('newsStore', () => {
  beforeEach(() => {
    useNewsStore.setState({ items: [] });
    vi.clearAllMocks();
  });

  it('initial state has empty items', () => {
    useNewsStore.setState({ items: [] });
    expect(useNewsStore.getState().items).toEqual([]);
  });

  it('addItem prepends and caps at 50', () => {
    // Fill with 50 items
    const initial = Array.from({ length: 50 }, (_, i) => makeItem(`old-${i}`));
    useNewsStore.setState({ items: initial });

    // Add one more
    useNewsStore.getState().addItem(makeItem('new-1', 'New item'));

    const items = useNewsStore.getState().items;
    expect(items.length).toBe(50);
    expect(items[0].id).toBe('new-1');
    // The last old item should have been dropped
    expect(items.some((it) => it.id === 'old-49')).toBe(false);
  });

  it('setItems replaces items', () => {
    useNewsStore.getState().addItem(makeItem('x'));
    expect(useNewsStore.getState().items.length).toBe(1);

    const replacement = [makeItem('a'), makeItem('b')];
    useNewsStore.getState().setItems(replacement);

    expect(useNewsStore.getState().items).toEqual(replacement);
  });

  it('clearItems empties array', () => {
    useNewsStore.getState().addItem(makeItem('x'));
    useNewsStore.getState().clearItems();
    expect(useNewsStore.getState().items).toEqual([]);
  });

  it('fetchNews calls API', async () => {
    const newsData: NewsItem[] = [makeItem('fetched-1')];
    mockApiGet.mockResolvedValueOnce(newsData);

    await useNewsStore.getState().fetchNews();

    expect(mockApiGet).toHaveBeenCalledWith('/api/news');
    expect(useNewsStore.getState().items).toEqual(newsData);
  });
});
