import { BACKEND_URL } from './api';

type EventListener = (data: any) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<EventListener>> = new Map();
  private reconnectInterval = 2000;
  private snapshot: any = null;

  constructor() {
    this.connect();
  }

  public connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }


    try {
      this.ws = new WebSocket(`${BACKEND_URL.replace(/^http/, 'ws')}/ws`);

      this.ws.onopen = () => {

        console.log('[WS] Connected to OSKA NEXUS Backend');
        this.emit('connection', { connected: true });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'initial_state') this.snapshot = data;
          if (data.type) {
            this.emit(data.type, data);
          }
        } catch (e) {
          console.error('[WS] Error parsing message:', e);
        }
      };

      this.ws.onclose = () => {

        this.emit('connection', { connected: false });
        setTimeout(() => this.connect(), this.reconnectInterval);
      };

      this.ws.onerror = () => {

      };
    } catch {
      setTimeout(() => this.connect(), this.reconnectInterval);
    }
  }

  public on(event: string, callback: EventListener) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback);
    if (event === 'initial_state' && this.snapshot) callback(this.snapshot);
    if (event === 'connection') callback({ connected: this.ws?.readyState === WebSocket.OPEN });
    return () => {
      this.listeners.get(event)?.delete(callback);
    };
  }

  private emit(event: string, data: any) {
    this.listeners.get(event)?.forEach((cb) => {
      try {
        cb(data);
      } catch (err) {
        console.error(`[WS] Error in listener for ${event}:`, err);
      }
    });
  }
}

export const wsClient = new WebSocketClient();
