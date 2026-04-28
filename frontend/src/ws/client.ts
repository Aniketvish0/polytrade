import type { ServerEvent, BackendEvent } from '@/types/ws';
import { WS_BASE_URL } from '@/utils/constants';

type AnyEvent = ServerEvent | BackendEvent;
type EventHandler = (event: AnyEvent) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Set<EventHandler> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseDelay = 1000;
  private token: string | null = null;
  private _isConnected = false;

  get isConnected(): boolean {
    return this._isConnected;
  }

  connect(token?: string): void {
    if (token) this.token = token;
    if (!this.token) return;
    if (this.ws?.readyState === WebSocket.OPEN) return;

    const url = `${WS_BASE_URL}?token=${encodeURIComponent(this.token)}`;

    try {
      this.ws = new WebSocket(url);

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
          const data = JSON.parse(event.data) as AnyEvent;
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
    this.reconnectAttempts = 0;
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.onmessage = null;
      this.ws.onopen = null;
      this.ws.close();
      this.ws = null;
    }
    this._isConnected = false;
    this.token = null;
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

  private dispatch(event: AnyEvent): void {
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
