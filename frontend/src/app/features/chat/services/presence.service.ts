import { Injectable, inject, signal, OnDestroy, DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ChatSocketService } from './chat-socket.service';
import { ChatService } from './chat.service';

export type PresenceStatus = 'online' | 'offline';

@Injectable({ providedIn: 'root' })
export class PresenceService implements OnDestroy {
  private readonly chatSocket = inject(ChatSocketService);
  private readonly chatService = inject(ChatService);
  private readonly destroyRef = inject(DestroyRef);

  /** userId → status map. Reactive signal for template reads. */
  private readonly _presenceMap = signal<Map<string, PresenceStatus>>(new Map());
  readonly presenceMap = this._presenceMap.asReadonly();

  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;

  constructor() {
    // Subscribe to real-time presence events from WS
    this.chatSocket.presenceChanged$.pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(evt => {
      this._presenceMap.update(m => {
        const next = new Map(m);
        next.set(evt.user_id, evt.status);
        return next;
      });
    });
  }

  /** Call after WS connects. Starts heartbeat and loads initial presence state. */
  start(): void {
    this.fetchPresence();
    this.startHeartbeat();
  }

  /** Returns the current status for a given userId. */
  getStatus(userId: string): PresenceStatus {
    return this._presenceMap().get(userId) ?? 'offline';
  }

  /** Manually update a user's status (e.g., from WS event already handled). */
  setStatus(userId: string, status: PresenceStatus): void {
    this._presenceMap.update(m => {
      const next = new Map(m);
      next.set(userId, status);
      return next;
    });
  }

  private fetchPresence(): void {
    this.chatService.getPresencia().subscribe({
      next: (statuses) => {
        this._presenceMap.update(() => {
          const m = new Map<string, PresenceStatus>();
          for (const [userId, status] of Object.entries(statuses)) {
            m.set(userId, status as PresenceStatus);
          }
          return m;
        });
      },
    });
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    // Send heartbeat every 25s (server TTL is 35s)
    this.heartbeatTimer = setInterval(() => {
      this.chatSocket.sendHeartbeat();
    }, 25_000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  ngOnDestroy(): void {
    this.stopHeartbeat();
  }
}
