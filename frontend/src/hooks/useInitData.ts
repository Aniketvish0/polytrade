import { useEffect } from 'react';
import { usePortfolioStore } from '@/stores/portfolioStore';
import { useTradeStore } from '@/stores/tradeStore';
import { useNewsStore } from '@/stores/newsStore';
import { usePolicyStore } from '@/stores/policyStore';
import { useStrategyStore } from '@/stores/strategyStore';
import { useAgentStore } from '@/stores/agentStore';
import { useAuthStore } from '@/stores/authStore';
import { authApi } from '@/api';

export function useInitData() {
  const fetchPortfolio = usePortfolioStore((s) => s.fetchPortfolio);
  const fetchPositions = usePortfolioStore((s) => s.fetchPositions);
  const fetchTrades = useTradeStore((s) => s.fetchTrades);
  const fetchApprovals = useTradeStore((s) => s.fetchApprovals);
  const fetchNews = useNewsStore((s) => s.fetchNews);
  const fetchPolicies = usePolicyStore((s) => s.fetchPolicies);
  const fetchStrategies = useStrategyStore((s) => s.fetchStrategies);
  const fetchStatus = useAgentStore((s) => s.fetchStatus);
  const setUser = useAuthStore((s) => s.setUser);

  useEffect(() => {
    authApi.me().then((user) => setUser(user)).catch(() => {});

    fetchPortfolio();
    fetchPositions();
    fetchTrades();
    fetchApprovals();
    fetchNews();
    fetchPolicies();
    fetchStrategies();
    fetchStatus();
  }, [fetchPortfolio, fetchPositions, fetchTrades, fetchApprovals, fetchNews, fetchPolicies, fetchStrategies, fetchStatus, setUser]);
}
