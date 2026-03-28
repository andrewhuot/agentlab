import type { BuilderEvent, BuilderEventType } from './builder-types';

const EVENT_TYPES: BuilderEventType[] = [
  'message.delta',
  'task.started',
  'task.progress',
  'plan.ready',
  'artifact.updated',
  'eval.started',
  'eval.completed',
  'approval.requested',
  'task.completed',
  'task.failed',
];

type EventHandler = (event: BuilderEvent) => void;

export interface BuilderStreamParams {
  sessionId?: string;
  taskId?: string;
  since?: number;
}

class BuilderWebSocketClient {
  private source: EventSource | null = null;
  private reconnectTimer: number | null = null;
  private readonly handlers: Map<BuilderEventType | '*', Set<EventHandler>> = new Map();
  private params: BuilderStreamParams = {};
  private shouldReconnect = true;

  connect(params?: BuilderStreamParams): void {
    if (params) {
      this.params = params;
    }

    this.disconnectSourceOnly();

    const query = new URLSearchParams();
    if (this.params.sessionId) query.set('session_id', this.params.sessionId);
    if (this.params.taskId) query.set('task_id', this.params.taskId);
    if (this.params.since !== undefined) query.set('since', String(this.params.since));

    const suffix = query.toString() ? `?${query.toString()}` : '';
    this.source = new EventSource(`/api/builder/events/stream${suffix}`);

    this.source.onmessage = (message) => {
      this.handleRawEvent(message.data);
    };

    for (const eventType of EVENT_TYPES) {
      this.source.addEventListener(eventType, (message) => {
        const data = (message as MessageEvent<string>).data;
        this.handleRawEvent(data, eventType);
      });
    }

    this.source.addEventListener('heartbeat', () => {
      // Keepalive events are intentionally ignored.
    });

    this.source.onerror = () => {
      if (!this.shouldReconnect) return;
      this.scheduleReconnect();
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.clearReconnectTimer();
    this.disconnectSourceOnly();
  }

  reconnect(): void {
    this.shouldReconnect = true;
    this.connect();
  }

  on(type: BuilderEventType | '*', handler: EventHandler): () => void {
    const existing = this.handlers.get(type) ?? new Set<EventHandler>();
    existing.add(handler);
    this.handlers.set(type, existing);
    return () => {
      const current = this.handlers.get(type);
      current?.delete(handler);
    };
  }

  private handleRawEvent(raw: string, fallbackType?: BuilderEventType): void {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(raw) as Record<string, unknown>;
    } catch {
      return;
    }

    const eventType = (parsed.type || fallbackType || 'message.delta') as BuilderEventType;
    const event: BuilderEvent = {
      event_id: String(parsed.id || parsed.event_id || crypto.randomUUID()),
      event_type: eventType,
      session_id: String(parsed.session_id || ''),
      task_id: parsed.task_id ? String(parsed.task_id) : null,
      payload: (parsed.payload || {}) as Record<string, unknown>,
      timestamp: Number(parsed.timestamp || Date.now() / 1000),
    };

    this.handlers.get(event.event_type)?.forEach((handler) => handler(event));
    this.handlers.get('*')?.forEach((handler) => handler(event));
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    this.disconnectSourceOnly();
    this.reconnectTimer = window.setTimeout(() => {
      if (!this.shouldReconnect) return;
      this.connect();
    }, 1500);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private disconnectSourceOnly(): void {
    if (this.source) {
      this.source.close();
      this.source = null;
    }
  }
}

export const builderWsClient = new BuilderWebSocketClient();
export type { EventHandler as BuilderEventHandler };
