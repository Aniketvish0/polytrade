import type { ServerEvent } from '@/types/ws';
import { useChatStore } from '@/stores/chatStore';
import { usePortfolioStore } from '@/stores/portfolioStore';
import { useTradeStore } from '@/stores/tradeStore';
import { useNewsStore } from '@/stores/newsStore';
import { useAgentStore } from '@/stores/agentStore';
import { usePolicyStore } from '@/stores/policyStore';
import { useStrategyStore } from '@/stores/strategyStore';
import { useNotificationStore } from '@/stores/notificationStore';

export function dispatchServerEvent(event: ServerEvent): void {
  switch (event.type) {
    case 'chat_message': {
      useChatStore.getState().addMessage(event.payload);
      useChatStore.getState().setIsAgentTyping(false);
      break;
    }

    case 'trade_update': {
      const trade = event.payload;
      useTradeStore.getState().addTrade(trade);

      if (trade.status === 'held') {
        useNotificationStore.getState().addToast({
          type: 'warning',
          title: 'Trade Held',
          message: `${trade.market} - ${trade.reason ?? 'Pending approval'}`,
        });
      } else if (trade.status === 'executed') {
        useNotificationStore.getState().addToast({
          type: 'success',
          title: 'Trade Executed',
          message: `${trade.side.toUpperCase()} ${trade.shares} ${trade.market}`,
        });
      } else if (trade.status === 'denied') {
        useNotificationStore.getState().addToast({
          type: 'error',
          title: 'Trade Denied',
          message: `${trade.market} - ${trade.reason ?? 'Policy violation'}`,
        });
      }
      break;
    }

    case 'approval_request': {
      useTradeStore.getState().addApproval(event.payload);
      useNotificationStore.getState().addToast({
        type: 'warning',
        title: 'Approval Required',
        message: event.payload.reason,
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
      if (event.payload.relevance > 0.8) {
        useNotificationStore.getState().addToast({
          type: 'info',
          title: 'Breaking News',
          message: event.payload.headline,
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
