import type { ServerEvent, BackendEvent } from '@/types/ws';
import type { AgentStatus } from '@/types/agent';
import { useChatStore } from '@/stores/chatStore';
import { usePortfolioStore } from '@/stores/portfolioStore';
import { useTradeStore } from '@/stores/tradeStore';
import { useNewsStore } from '@/stores/newsStore';
import { useAgentStore } from '@/stores/agentStore';
import { usePolicyStore } from '@/stores/policyStore';
import { useStrategyStore } from '@/stores/strategyStore';
import { useNotificationStore } from '@/stores/notificationStore';

/**
 * Maps a backend event (domain:action format) to internal ServerEvent(s)
 * and dispatches them to the appropriate stores.
 */
export function dispatchServerEvent(raw: ServerEvent | BackendEvent): void {
  // If it uses the backend's "domain:action" format with `data`, normalize first
  if ('data' in raw && typeof raw.data === 'object' && raw.data !== null) {
    dispatchBackendEvent(raw as BackendEvent);
    return;
  }

  // Otherwise handle the internal format (with `payload`)
  const event = raw as ServerEvent;
  handleInternalEvent(event);
}

function dispatchBackendEvent(event: BackendEvent): void {
  const { type, data } = event;

  switch (type) {
    case 'agent:status': {
      useAgentStore.getState().setStatus(data.status as AgentStatus);
      useAgentStore.getState().setCurrentTask((data.currentTask as string) ?? null);
      break;
    }

    case 'agent:message': {
      const msg = {
        id: (data.id as string) ?? `agent-${Date.now()}`,
        role: 'agent' as const,
        type: 'text' as const,
        content: (data.content as string) ?? (data.message as string) ?? '',
        data: data.data as Record<string, unknown> | undefined,
        timestamp: Date.now(),
      };
      useChatStore.getState().addMessage(msg);
      useChatStore.getState().setIsAgentTyping(false);
      break;
    }

    case 'trade:executed': {
      const trade = data as Record<string, unknown>;
      const mapped = {
        ...trade,
        status: 'executed' as const,
      };
      useTradeStore.getState().addTrade(mapped as never);
      useNotificationStore.getState().addToast({
        type: 'success',
        title: 'Trade Executed',
        message: `${(trade.side as string)?.toUpperCase() ?? ''} ${trade.shares ?? ''} ${trade.market ?? ''}`,
      });
      break;
    }

    case 'trade:held': {
      const trade = data as Record<string, unknown>;
      const mapped = {
        ...trade,
        status: 'held' as const,
      };
      useTradeStore.getState().addTrade(mapped as never);

      // Also create an approval request
      if (trade.approval_id || trade.id) {
        useTradeStore.getState().addApproval({
          id: (trade.approval_id as string) ?? `approval-${trade.id}`,
          tradeId: trade.id as string,
          trade: mapped as never,
          reason: (trade.reason as string) ?? 'Pending approval',
          riskScore: (trade.risk_score as number) ?? 0,
          policyViolations: (trade.policy_violations as string[]) ?? (trade.policyFlags as string[]) ?? [],
          timestamp: Date.now(),
        });
      }

      useNotificationStore.getState().addToast({
        type: 'warning',
        title: 'Trade Held',
        message: `${trade.market ?? ''} - ${(trade.reason as string) ?? 'Pending approval'}`,
        duration: 10000,
      });
      break;
    }

    case 'trade:denied': {
      const trade = data as Record<string, unknown>;
      const mapped = {
        ...trade,
        status: 'denied' as const,
      };
      useTradeStore.getState().addTrade(mapped as never);
      useNotificationStore.getState().addToast({
        type: 'error',
        title: 'Trade Denied',
        message: `${trade.market ?? ''} - ${(trade.reason as string) ?? 'Policy violation'}`,
      });
      break;
    }

    case 'portfolio:update': {
      usePortfolioStore.getState().setSummary(data as never);
      break;
    }

    case 'news:item': {
      useNewsStore.getState().addItem(data as never);
      const relevance = data.relevance as number;
      if (relevance && relevance > 0.8) {
        useNotificationStore.getState().addToast({
          type: 'info',
          title: 'Breaking News',
          message: data.headline as string,
        });
      }
      break;
    }

    case 'policy:updated': {
      const policies = (data.policies ?? data) as never;
      if (Array.isArray(policies)) {
        usePolicyStore.getState().setPolicies(policies);
      }
      break;
    }

    case 'strategy:updated': {
      const strategies = (data.strategies ?? data) as never;
      if (Array.isArray(strategies)) {
        useStrategyStore.getState().setStrategies(strategies);
      }
      break;
    }

    case 'approval:approved': {
      const approvalId = (data.approval_id ?? data.id) as string;
      if (approvalId) {
        useTradeStore.getState().removeApproval(approvalId);
      }
      const tradeId = data.trade_id as string;
      if (tradeId) {
        useTradeStore.getState().updateTrade(tradeId, { status: 'approved' });
      }
      useNotificationStore.getState().addToast({
        type: 'success',
        title: 'Trade Approved',
        message: (data.message as string) ?? 'Trade has been approved',
      });
      break;
    }

    case 'approval:rejected': {
      const approvalId = (data.approval_id ?? data.id) as string;
      if (approvalId) {
        useTradeStore.getState().removeApproval(approvalId);
      }
      const tradeId = data.trade_id as string;
      if (tradeId) {
        useTradeStore.getState().updateTrade(tradeId, { status: 'denied' });
      }
      useNotificationStore.getState().addToast({
        type: 'error',
        title: 'Trade Rejected',
        message: (data.message as string) ?? 'Trade has been rejected',
      });
      break;
    }

    case 'pong': {
      // Heartbeat response — ignore
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

/** Handle legacy internal format events (with payload field) */
function handleInternalEvent(event: ServerEvent): void {
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
