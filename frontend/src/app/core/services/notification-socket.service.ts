import { Injectable, signal, inject, OnDestroy } from '@angular/core';
import { AuthService } from '../auth/auth.service';
import { environment } from '../../../environments/environment';

export interface WsNotification {
  id: string;
  tipo: string;
  titulo: string;
  mensaje: string;
  url_accion?: string;
  ancla?: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
}

interface WsMessage {
  type: string;
  data: WsNotification;
}

@Injectable({ providedIn: 'root' })
export class NotificationSocketService implements OnDestroy {
  private readonly auth = inject(AuthService);

  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  // ── Signals ───────────────────────────────────────────────────
  private readonly _isConnected = signal(false);
  private readonly _unreadCount = signal(0);
  private readonly _latestNotification = signal<WsNotification | null>(null);

  readonly isConnected = this._isConnected.asReadonly();
  readonly unreadCount = this._unreadCount.asReadonly();
  readonly latestNotification = this._latestNotification.asReadonly();

  // ── Reconnection config ───────────────────────────────────────
  private static readonly BASE_DELAY = 2000;
  private static readonly MAX_DELAY = 30000;
  private static readonly AUTH_FAILURE_CODE = 4001;

  // ── Public API ────────────────────────────────────────────────

  connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN) return;

    const token = this.auth.getAccessToken();
    if (!token) return;

    this.intentionalClose = false;
    const url = `${environment.wsUrl}/ws/notifications/?token=${token}`;

    this.socket = new WebSocket(url);

    this.socket.onopen = (): void => {
      this._isConnected.set(true);
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event: MessageEvent): void => {
      try {
        const msg = JSON.parse(event.data as string) as WsMessage;
        if (msg.type === 'notification') {
          this._latestNotification.set(msg.data);
          this._unreadCount.update(count => count + 1);
        }
      } catch {
        // Ignore malformed messages
      }
    };

    this.socket.onclose = (event: CloseEvent): void => {
      this._isConnected.set(false);
      this.socket = null;

      if (event.code === NotificationSocketService.AUTH_FAILURE_CODE || this.intentionalClose) {
        return;
      }

      this.scheduleReconnect();
    };

    this.socket.onerror = (): void => {
      // onclose fires after onerror; reconnection is handled there
    };
  }

  disconnect(): void {
    this.intentionalClose = true;
    this.clearReconnectTimer();
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this._isConnected.set(false);
  }

  /** Reset unread count (e.g., after user views notification panel). */
  resetUnreadCount(): void {
    this._unreadCount.set(0);
  }

  /** Set unread count from server (e.g., initial load from REST API). */
  setUnreadCount(count: number): void {
    this._unreadCount.set(count);
  }

  ngOnDestroy(): void {
    this.disconnect();
  }

  // ── Private ───────────────────────────────────────────────────

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    const delay = Math.min(
      NotificationSocketService.BASE_DELAY * Math.pow(2, this.reconnectAttempts),
      NotificationSocketService.MAX_DELAY,
    );
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
