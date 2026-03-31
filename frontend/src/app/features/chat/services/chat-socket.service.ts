import { ApplicationRef, Injectable, NgZone, signal, inject, OnDestroy } from '@angular/core';
import { Subject } from 'rxjs';
import { AuthService } from '../../../core/auth/auth.service';
import { environment } from '../../../../environments/environment';
import { Mensaje, ChatTypingEvent, ChatReadEvent } from '../models/chat.models';

export interface ChatMessageEditedEvent {
  mensaje_id: string;
  contenido: string;
  contenido_html: string;
  editado_at: string;
}

export interface ChatPresenceEvent {
  user_id: string;
  status: 'online' | 'offline';
}

@Injectable({ providedIn: 'root' })
export class ChatSocketService implements OnDestroy {
  private readonly auth = inject(AuthService);
  private readonly zone = inject(NgZone);
  private readonly appRef = inject(ApplicationRef);

  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private typingClearTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  // ── Signals (for values read directly by templates via computed()) ──────
  private readonly _isConnected = signal(false);
  // Custom equality: same user+conversation → no extra CD cycle per keystroke
  private readonly _typingEvent = signal<ChatTypingEvent | null>(null, {
    equal: (a, b) =>
      a === b ||
      (a !== null && b !== null &&
       a.conversacion_id === b.conversacion_id &&
       a.user_id === b.user_id),
  });
  private readonly _newConversation = signal<Record<string, unknown> | null>(null);

  readonly isConnected = this._isConnected.asReadonly();
  readonly typingEvent = this._typingEvent.asReadonly();
  readonly newConversation = this._newConversation.asReadonly();

  // ── Subjects (for values consumed via RxJS subscriptions) ────────────────
  // Using Subject + zone.run() instead of signal + toObservable() because:
  // toObservable() runs its internal effect AFTER view rendering. When the
  // effect calls signal.update(), a second tick is needed but is not always
  // scheduled reliably. With a Subject, zone.run(() => subject.next(value))
  // calls subscribers synchronously — messages.update() runs BEFORE the tick,
  // so the view renders with the correct data in the very next tick.
  readonly newMessage$ = new Subject<Mensaje>();
  readonly readEvent$ = new Subject<ChatReadEvent>();
  readonly messageEdited$ = new Subject<ChatMessageEditedEvent>();
  readonly presenceChanged$ = new Subject<ChatPresenceEvent>();

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
    const url = `${environment.wsUrl}/ws/chat/?token=${token}`;

    // WebSocket is created outside Angular zone so zone.js does NOT patch its
    // callbacks — prevents zone from calling ApplicationRef.tick() on every
    // message event (including rapid typing), which caused the browser freeze.
    this.zone.runOutsideAngular(() => {
      this.socket = new WebSocket(url);

      this.socket.onopen = (): void => {
        this._isConnected.set(true);
        this.reconnectAttempts = 0;
      };

      this.socket.onmessage = (event: MessageEvent): void => {
        try {
          const msg = JSON.parse(event.data as string) as Record<string, unknown>;
          const type = msg['type'] as string;

          if (type === 'new_message' && msg['data']) {
            // zone.run() so RxJS subscribers run inside Angular zone.
            // Subject.next() is synchronous: subscribers execute immediately,
            // updating component signals BEFORE the subsequent tick renders views.
            // appRef.tick() forces an immediate CD cycle — zone.js does NOT schedule
            // ticks for WS callbacks created in runOutsideAngular(), so markForCheck()
            // alone is insufficient.
            this.zone.run(() => {
              this.newMessage$.next(msg['data'] as Mensaje);
              this.appRef.tick();
            });

          } else if (type === 'typing' && msg['data']) {
            // Typing stays OUTSIDE zone — fires on every keystroke and is
            // read directly by a computed() in the template; does not need zone.
            const typingData = msg['data'] as ChatTypingEvent;
            this._typingEvent.set(typingData);
            // Single rolling timer: cancel the previous before setting a new one,
            // so rapid typing never accumulates more than one pending timer.
            if (this.typingClearTimer !== null) clearTimeout(this.typingClearTimer);
            this.typingClearTimer = setTimeout(() => {
              this.typingClearTimer = null;
              const current = this._typingEvent();
              if (current && current.conversacion_id === typingData.conversacion_id) {
                this._typingEvent.set(null);
              }
            }, 5000);

          } else if (type === 'message_read' && msg['data']) {
            this.zone.run(() => {
              this.readEvent$.next(msg['data'] as ChatReadEvent);
              this.appRef.tick();
            });

          } else if (type === 'new_conversation' && msg['data']) {
            this.zone.run(() => this._newConversation.set(msg['data'] as Record<string, unknown>));

          } else if (type === 'message_edited' && msg['data']) {
            this.zone.run(() => {
              this.messageEdited$.next(msg['data'] as ChatMessageEditedEvent);
              this.appRef.tick();
            });

          } else if (type === 'presence_changed' && msg['data']) {
            // Presence updates are high-frequency; use signal for direct template reads
            const evt = msg['data'] as ChatPresenceEvent;
            this.zone.run(() => {
              this.presenceChanged$.next(evt);
              this.appRef.tick();
            });
          }
        } catch {
          // Ignore malformed messages
        }
      };

      this.socket.onclose = (event: CloseEvent): void => {
        this._isConnected.set(false);
        this.socket = null;

        if (event.code === ChatSocketService.AUTH_FAILURE_CODE || this.intentionalClose) {
          return;
        }
        this.zone.runOutsideAngular(() => this.scheduleReconnect());
      };

      this.socket.onerror = (): void => {
        // onclose fires after onerror; reconnection is handled there
      };
    });
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

  sendMessage(conversacionId: string, contenido: string, imagenUrl?: string, respondeAId?: string): void {
    this.send({
      type: 'chat.send_message',
      conversacion_id: conversacionId,
      contenido,
      imagen_url: imagenUrl ?? '',
      responde_a_id: respondeAId ?? null,
    });
  }

  sendTyping(conversacionId: string): void {
    this.send({ type: 'chat.typing', conversacion_id: conversacionId });
  }

  markRead(mensajeId: string): void {
    this.send({ type: 'chat.mark_read', mensaje_id: mensajeId });
  }

  joinConversation(conversacionId: string): void {
    this.send({ type: 'chat.join_conversation', conversacion_id: conversacionId });
  }

  sendHeartbeat(): void {
    this.send({ type: 'chat.heartbeat' });
  }

  ngOnDestroy(): void {
    this.disconnect();
  }

  // ── Private ───────────────────────────────────────────────────

  private send(data: Record<string, unknown>): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    const delay = Math.min(
      ChatSocketService.BASE_DELAY * Math.pow(2, this.reconnectAttempts),
      ChatSocketService.MAX_DELAY,
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
