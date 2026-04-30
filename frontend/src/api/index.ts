import { apiClient } from './client';
import type { AuthUser } from '@/stores/authStore';
import type { PortfolioSummary, Position } from '@/types/portfolio';
import type { Trade, ApprovalRequest } from '@/types/trade';
import type { NewsItem } from '@/types/news';
import type { Policy, Strategy } from '@/types/ws';
import type { EnhancedMarket } from '@/types/market';

// Auth
export const authApi = {
  me: () => apiClient.get<AuthUser>('/api/auth/me'),
};

// News
export const newsApi = {
  list: () => apiClient.get<NewsItem[]>('/api/news'),
};

// Portfolio
export const portfolioApi = {
  getSummary: () => apiClient.get<PortfolioSummary>('/api/portfolio/summary'),
  getPositions: () => apiClient.get<Position[]>('/api/portfolio/positions'),
};

// Trades
export const tradesApi = {
  list: () => apiClient.get<Trade[]>('/api/trades'),
  getById: (id: string) => apiClient.get<Trade>(`/api/trades/${id}`),
  approve: (id: string) => apiClient.post<Trade>(`/api/trades/${id}/approve`),
  deny: (id: string, reason?: string) =>
    apiClient.post<Trade>(`/api/trades/${id}/deny`, { reason }),
  getPendingApprovals: () =>
    apiClient.get<ApprovalRequest[]>('/api/trades/approvals'),
};

// Policies
export const policiesApi = {
  list: () => apiClient.get<Policy[]>('/api/policies'),
  update: (id: string, data: Partial<Policy>) =>
    apiClient.put<Policy>(`/api/policies/${id}`, data),
  toggle: (id: string) => apiClient.post<Policy>(`/api/policies/${id}/toggle`),
};

// Strategies
export const strategiesApi = {
  list: () => apiClient.get<Strategy[]>('/api/strategies'),
  update: (id: string, data: Partial<Strategy>) =>
    apiClient.put<Strategy>(`/api/strategies/${id}`, data),
  toggle: (id: string) =>
    apiClient.post<Strategy>(`/api/strategies/${id}/toggle`),
};

// Agent
export const agentApi = {
  getStatus: () =>
    apiClient.get<{ status: string; currentTask: string | null }>(
      '/api/agent/status'
    ),
  pause: () => apiClient.post('/api/agent/pause'),
  resume: () => apiClient.post('/api/agent/resume'),
};

// Markets
export const marketsApi = {
  listEnhanced: (params?: { category?: string; sort_by?: string; limit?: number }) => {
    const query: Record<string, string> = {};
    if (params?.category) query.category = params.category;
    if (params?.sort_by) query.sort_by = params.sort_by;
    if (params?.limit) query.limit = String(params.limit);
    return apiClient.get<EnhancedMarket[]>('/api/markets/enhanced', query);
  },
};

// Chat
export const chatApi = {
  send: (message: string) =>
    apiClient.post<{ id: string }>('/api/chat', { message }),
  getHistory: () => apiClient.get<unknown[]>('/api/chat/history'),
};
