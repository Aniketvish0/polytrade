import type { ServerEvent } from '@/types/ws';
import { WS_URL } from '@/utils/constants';

type EventHandler = (event: ServerEvent) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Set<EventHandler> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseDelay = 1000;
  private url: string;
  private _isConnected = false;

  constructor(url?: string) {
    this.url = url ?? WS_URL;
  }

  get isConnected(): boolean {
    return this._isConnected;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this._isConnected = true;
        this.reconnectAttempts = 0;
        this.dispatch({
          type: 'agent_status',
          payload: { status: 'idle', currentTask: null },
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as ServerEvent;
          this.dispatch(data);
        } catch {
          console.error('[WS] Failed to parse message:', event.data);
        }
      };

      this.ws.onclose = () => {
        this._isConnected = false;
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this._isConnected = false;
      };
    } catch {
      this._isConnected = false;
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._isConnected = false;
  }

  send(data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('[WS] Cannot send, not connected');
    }
  }

  on(handler: EventHandler): () => void {
    this.handlers.add(handler);
    return () => {
      this.handlers.delete(handler);
    };
  }

  private dispatch(event: ServerEvent): void {
    this.handlers.forEach((handler) => {
      try {
        handler(event);
      } catch (err) {
        console.error('[WS] Handler error:', err);
      }
    });
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;

    const delay = this.baseDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, Math.min(delay, 30000));
  }
}

export const wsClient = new WebSocketClient();
