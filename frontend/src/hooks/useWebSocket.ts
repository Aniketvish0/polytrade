import { useEffect, useRef } from 'react';
import { wsClient } from '@/ws/client';
import { dispatchServerEvent } from '@/ws/handlers';
import { useAgentStore } from '@/stores/agentStore';
import { useAuthStore } from '@/stores/authStore';

export function useWebSocket() {
  const setConnectionState = useAgentStore((s) => s.setConnectionState);
  const token = useAuthStore((s) => s.token);
  const prevTokenRef = useRef<string | null>(null);

  useEffect(() => {
    if (!token) return;

    // Reconnect if token changed
    if (prevTokenRef.current && prevTokenRef.current !== token) {
      wsClient.disconnect();
    }
    prevTokenRef.current = token;

    setConnectionState('connecting');

    const unsubscribe = wsClient.on((event) => {
      if ('payload' in event && (event as Record<string, unknown>).type === 'agent_status') {
        setConnectionState('connected');
      }
      dispatchServerEvent(event);
    });

    wsClient.connect(token);

    const heartbeatCheck = setInterval(() => {
      if (wsClient.isConnected) {
        setConnectionState('connected');
      } else {
        setConnectionState('disconnected');
      }
    }, 5000);

    return () => {
      unsubscribe();
      clearInterval(heartbeatCheck);
      wsClient.disconnect();
    };
  }, [token, setConnectionState]);
}
