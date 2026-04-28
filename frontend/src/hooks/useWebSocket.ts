import { useEffect, useRef } from 'react';
import { wsClient } from '@/ws/client';
import { dispatchServerEvent } from '@/ws/handlers';
import { useAgentStore } from '@/stores/agentStore';

export function useWebSocket() {
  const setConnectionState = useAgentStore((s) => s.setConnectionState);
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    setConnectionState('connecting');

    const unsubscribe = wsClient.on((event) => {
      dispatchServerEvent(event);
    });

    wsClient.connect();

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
  }, [setConnectionState]);
}
