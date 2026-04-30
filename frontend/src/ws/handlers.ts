import type { ServerEvent, BackendEvent } from '@/types/ws';
import type { AgentStatus } from '@/types/agent';
import type { Trade } from '@/types/trade';
import type { NewsItem } from '@/types/news';
import { useAuthStore } from '@/stores/authStore';
import { useChatStore } from '@/stores/chatStore';
import { usePortfolioStore } from '@/stores/portfolioStore';
import { useTradeStore } from '@/stores/tradeStore';
import { useNewsStore } from '@/stores/newsStore';
import { useAgentStore } from '@/stores/agentStore';
import { usePolicyStore } from '@/stores/policyStore';
import { useStrategyStore } from '@/stores/strategyStore';
import { useNotificationStore } from '@/stores/notificationStore';
import { useActivityStore } from '@/stores/activityStore';

export function dispatchServerEvent(raw: ServerEvent | BackendEvent): void {
  if ('data' in raw && typeof raw.data === 'object' && raw.data !== null) {
    dispatchBackendEvent(raw as BackendEvent);
    return;
  }

  const event = raw as ServerEvent;
  handleInternalEvent(event);
}

function dispatchBackendEvent(event: BackendEvent): void {
  const { type, data } = event;

  switch (type) {
    case 'agent:status': {
      useAgentStore.getState().setStatus(data.status as AgentStatus);
      useAgentStore.getState().setCurrentTask((data.current_task as string) ?? (data.currentTask as string) ?? null);
      break;
    }

    case 'agent:activity': {
      const { phase, message, ...rest } = data as { phase: string; message: string; [k: string]: unknown };
      useActivityStore.getState().addEntry(phase, message, rest);
      break;
    }

    case 'agent:message': {
      const inner = (typeof data.message === 'object' && data.message !== null)
        ? (data.message as Record<string, unknown>)
        : data;
      const msg = {
        id: `agent-${Date.now()}`,
        role: 'agent' as const,
        type: ((inner.message_type as string) ?? 'text') as import('@/types/chat').MessageType,
        content: (inner.content as string) ?? '',
        data: (inner.data as Record<string, unknown>) ?? (inner.action as Record<string, unknown>) ?? undefined,
        timestamp: Date.now(),
      };
      useChatStore.getState().addMessage(msg);
      useChatStore.getState().setIsAgentTyping(false);
      break;
    }

    case 'trade:executed': {
      const inner = (data.trade ?? data) as Record<string, unknown>;
      const trade = inner as unknown as Trade;
      useTradeStore.getState().addTrade(trade);
      usePortfolioStore.getState().fetchPortfolio();
      usePortfolioStore.getState().fetchPositions();
      useNotificationStore.getState().addToast({
        type: 'success',
        title: 'Trade Executed',
        message: `${trade.action?.toUpperCase() ?? 'BUY'} ${trade.shares ?? ''} ${trade.market_question ?? ''}`,
      });
      break;
    }

    case 'trade:held': {
      const inner = (data.trade ?? data) as Record<string, unknown>;
      useTradeStore.getState().fetchApprovals();
      useNotificationStore.getState().addToast({
        type: 'warning',
        title: 'Trade Held',
        message: `${(inner.market_question as string) ?? ''} — ${(data.reason as string) ?? 'Pending approval'}`,
        duration: 10000,
      });
      break;
    }

    case 'trade:denied': {
      const inner = (data.trade ?? data) as Record<string, unknown>;
      useNotificationStore.getState().addToast({
        type: 'error',
        title: 'Trade Denied',
        message: `${(inner.market_question as string) ?? ''} — ${(data.reason as string) ?? 'Policy violation'}`,
      });
      break;
    }

    case 'portfolio:update': {
      usePortfolioStore.getState().fetchPortfolio();
      usePortfolioStore.getState().fetchPositions();
      break;
    }

    case 'news:item': {
      const item = data as unknown as NewsItem;
      useNewsStore.getState().addItem(item);
      const relevance = item.relevance_score ?? 0;
      if (relevance > 0.8) {
        useNotificationStore.getState().addToast({
          type: 'info',
          title: 'Breaking News',
          message: item.title,
        });
      }
      break;
    }

    case 'policy:updated': {
      usePolicyStore.getState().fetchPolicies();
      break;
    }

    case 'strategy:updated': {
      useStrategyStore.getState().fetchStrategies();
      break;
    }

    case 'onboarding:complete': {
      const user = useAuthStore.getState().user;
      if (user) {
        useAuthStore.getState().setUser({ ...user, onboarding_completed: true });
      }
      break;
    }

    case 'approval:approved': {
      const approvalId = (data.approval_id ?? data.id) as string;
      if (approvalId) {
        useTradeStore.getState().removeApproval(approvalId);
      }
      useTradeStore.getState().fetchTrades();
      usePortfolioStore.getState().fetchPortfolio();
      useNotificationStore.getState().addToast({
        type: 'success',
        title: 'Trade Approved',
        message: (data.message as string) ?? 'Trade has been approved and executed',
      });
      break;
    }

    case 'approval:rejected': {
      const approvalId = (data.approval_id ?? data.id) as string;
      if (approvalId) {
        useTradeStore.getState().removeApproval(approvalId);
      }
      useNotificationStore.getState().addToast({
        type: 'error',
        title: 'Trade Rejected',
        message: (data.message as string) ?? 'Trade has been rejected',
      });
      break;
    }

    case 'pong': {
      break;
    }

    case 'error': {
      useNotificationStore.getState().addToast({
        type: 'error',
        title: 'Error',
        message: (data.message as string) ?? 'Unknown error',
      });
      useChatStore.getState().addMessage({
        id: `err-${Date.now()}`,
        role: 'system',
        type: 'error',
        content: (data.message as string) ?? 'Unknown error',
        timestamp: Date.now(),
      });
      break;
    }

    default: {
      console.warn('[WS] Unhandled backend event type:', type, data);
      break;
    }
  }
}

function handleInternalEvent(event: ServerEvent): void {
  switch (event.type) {
    case 'chat_message': {
      useChatStore.getState().addMessage(event.payload);
      useChatStore.getState().setIsAgentTyping(false);
      break;
    }

    case 'trade_update': {
      useTradeStore.getState().addTrade(event.payload);
      break;
    }

    case 'approval_request': {
      useTradeStore.getState().addApproval(event.payload);
      useNotificationStore.getState().addToast({
        type: 'warning',
        title: 'Approval Required',
        message: event.payload.reasoning ?? 'Trade requires approval',
        duration: 10000,
      });
      break;
    }

    case 'portfolio_update': {
      usePortfolioStore.getState().setSummary(event.payload);
      break;
    }

    case 'position_update': {
      usePortfolioStore.getState().updatePosition(event.payload);
      break;
    }

    case 'news_item': {
      useNewsStore.getState().addItem(event.payload);
      if ((event.payload.relevance_score ?? 0) > 0.8) {
        useNotificationStore.getState().addToast({
          type: 'info',
          title: 'Breaking News',
          message: event.payload.title,
        });
      }
      break;
    }

    case 'agent_status': {
      useAgentStore.getState().setStatus(event.payload.status);
      useAgentStore.getState().setCurrentTask(event.payload.currentTask);
      break;
    }

    case 'heartbeat': {
      useAgentStore.getState().setHeartbeat(event.payload.timestamp);
      break;
    }

    case 'error': {
      useNotificationStore.getState().addToast({
        type: 'error',
        title: 'Error',
        message: event.payload.message,
      });
      useChatStore.getState().addMessage({
        id: `err-${Date.now()}`,
        role: 'system',
        type: 'error',
        content: event.payload.message,
        timestamp: Date.now(),
      });
      break;
    }

    case 'policy_update': {
      usePolicyStore.getState().setPolicies(event.payload.policies);
      break;
    }

    case 'strategy_update': {
      useStrategyStore.getState().setStrategies(event.payload.strategies);
      break;
    }
  }
}
