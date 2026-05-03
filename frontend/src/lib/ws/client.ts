import type { WSClientMessage, WSServerMessage } from "../api/types";

type Listener = (msg: WSServerMessage) => void;
type StateListener = (state: WSState) => void;

export type WSState = "idle" | "connecting" | "open" | "closed" | "error";

export interface WSClientOptions {
  url: string;
  reconnectDelayMs?: number;
  maxReconnectDelayMs?: number;
}

export class STSWebSocket {
  private socket: WebSocket | null = null;
  private listeners = new Set<Listener>();
  private stateListeners = new Set<StateListener>();
  private state: WSState = "idle";
  private reconnectAttempts = 0;
  private shouldReconnect = true;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(private readonly options: WSClientOptions) {}

  connect(): void {
    this.shouldReconnect = true;
    this.open();
  }

  close(): void {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
    this.setState("closed");
  }

  send(msg: WSClientMessage): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error("websocket not open");
    }
    this.socket.send(JSON.stringify(msg));
  }

  onMessage(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  onState(listener: StateListener): () => void {
    this.stateListeners.add(listener);
    listener(this.state);
    return () => this.stateListeners.delete(listener);
  }

  private open(): void {
    this.setState("connecting");
    const socket = new WebSocket(this.options.url);
    this.socket = socket;

    socket.addEventListener("open", () => {
      this.reconnectAttempts = 0;
      this.setState("open");
    });

    socket.addEventListener("message", (event) => {
      let parsed: WSServerMessage;
      try {
        parsed = JSON.parse(event.data) as WSServerMessage;
      } catch {
        return;
      }
      for (const l of this.listeners) l(parsed);
    });

    socket.addEventListener("error", () => {
      this.setState("error");
    });

    socket.addEventListener("close", () => {
      this.setState("closed");
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    });
  }

  private scheduleReconnect(): void {
    const baseDelay = this.options.reconnectDelayMs ?? 500;
    const maxDelay = this.options.maxReconnectDelayMs ?? 8000;
    const delay = Math.min(maxDelay, baseDelay * 2 ** this.reconnectAttempts);
    this.reconnectAttempts += 1;
    this.reconnectTimer = setTimeout(() => this.open(), delay);
  }

  private setState(state: WSState): void {
    if (state === this.state) return;
    this.state = state;
    for (const l of this.stateListeners) l(state);
  }
}

export function buildWsUrl(path: string): string {
  if (typeof window === "undefined") return path;
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}${path}`;
}
