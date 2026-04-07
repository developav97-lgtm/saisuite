import {
  ApplicationRef, ChangeDetectionStrategy, ChangeDetectorRef, Component, DestroyRef,
  inject, signal, computed, OnInit, OnDestroy, input, output, effect,
} from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { debounceTime, distinctUntilChanged, filter } from 'rxjs';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { ChatListComponent } from '../chat-list/chat-list.component';
import { ChatWindowComponent } from '../chat-window/chat-window.component';
import { ChatSearchComponent } from '../chat-search/chat-search.component';
import { ChatService } from '../../services/chat.service';
import { ChatSocketService } from '../../services/chat-socket.service';
import { PresenceService } from '../../services/presence.service';
import { AuthService } from '../../../../core/auth/auth.service';
import { ChatStateService } from '../../../../core/services/chat-state.service';
import { Conversacion } from '../../models/chat.models';

@Component({
  selector: 'app-chat-panel',
  imports: [
    MatIconModule, MatButtonModule,
    ChatListComponent, ChatWindowComponent, ChatSearchComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="chat-panel" [class.chat-panel--open]="isOpen()">
      <div class="chat-panel__header">
        @if (activeConversacion()) {
          <button mat-icon-button (click)="backToList()">
            <mat-icon>arrow_back</mat-icon>
          </button>
          @if (activeConversacion()!.bot_context) {
            <mat-icon class="chat-panel__icon">smart_toy</mat-icon>
            <div class="chat-panel__peer">
              <span class="chat-panel__title">{{ peerName() }}</span>
              <span class="chat-panel__status chat-panel__status--online">En línea</span>
            </div>
          } @else {
            <div class="chat-panel__peer">
              <span class="chat-panel__title">{{ peerName() }}</span>
              <span class="chat-panel__status"
                    [class.chat-panel__status--online]="peerStatus() === 'online'">
                {{ peerStatus() === 'online' ? 'En línea' : 'Desconectado' }}
              </span>
            </div>
          }
          <span class="spacer"></span>
          <button mat-icon-button
                  [class.chat-panel__search-active]="searchOpen()"
                  (click)="toggleSearch()">
            <mat-icon>search</mat-icon>
          </button>
          <button mat-icon-button (click)="close.emit()">
            <mat-icon>close</mat-icon>
          </button>
        } @else {
          <mat-icon class="chat-panel__icon">chat</mat-icon>
          <span class="chat-panel__title">Chat</span>
          <span class="spacer"></span>
          <button mat-icon-button (click)="close.emit()">
            <mat-icon>close</mat-icon>
          </button>
        }
      </div>

      @if (searchOpen() && activeConversacion()) {
        <app-chat-search
          [conversacionId]="activeConversacion()!.id"
          (close)="searchOpen.set(false)"
          (jumpToMessage)="onJumpToMessage($event)" />
      }

      <div class="chat-panel__body">
        @if (activeConversacion()) {
          <app-chat-window
            [conversacion]="activeConversacion()!"
            [currentUserId]="currentUserId()"
            [jumpToId]="jumpTarget()"
            (back)="backToList()" />
        } @else {
          <app-chat-list
            [conversaciones]="conversaciones()"
            [currentUserId]="currentUserId()"
            [loading]="loadingConversaciones()"
            (selectConversacion)="openConversacion($event)"
            (buscarUsuario)="buscarYCrearConversacion($event)" />
        }
      </div>
    </div>
  `,
  styles: [`
    .chat-panel {
      position: fixed;
      right: -420px;
      bottom: 0;
      width: 420px;
      height: calc(100vh - 64px);
      top: 64px;
      border-radius: 12px;
      background: var(--sc-surface-card, #fff);
      border-left: 1px solid var(--sc-surface-border, #e2e8f0);
      box-shadow: -4px 0 16px rgba(0, 0, 0, 0.08);
      z-index: 999;
      display: flex;
      flex-direction: column;
      transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);

      &--open {
        right: 0;
      }
    }

    .chat-panel__header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      border-bottom: 1px solid var(--sc-surface-border, #e2e8f0);
      background: var(--sc-surface-header, #e2e9f3);
      border-radius: 12px 12px 0 0;
      min-height: 56px;
    }

    .chat-panel__icon {
      color: var(--sc-primary, #1565c0);
    }

    .chat-panel__title {
      font-weight: 600;
      font-size: 1rem;
      color: var(--sc-text-color, #1a202c);
    }

    .spacer {
      flex: 1;
    }

    .chat-panel__peer {
      display: flex;
      flex-direction: column;
      gap: 1px;
    }

    .chat-panel__status {
      font-size: 0.7rem;
      color: var(--sc-text-muted, #718096);

      &--online {
        color: #22c55e;
      }
    }

    .chat-panel__search-active {
      color: var(--sc-primary, #1565c0);
    }

    .chat-panel__body {
      flex: 1;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    @media (max-width: 480px) {
      .chat-panel {
        width: 100vw;
        right: -100vw;

        &--open {
          right: 0;
        }
      }
    }
  `],
})
export class ChatPanelComponent implements OnInit, OnDestroy {
  private readonly chatService = inject(ChatService);
  private readonly chatSocket = inject(ChatSocketService);
  private readonly authService = inject(AuthService);
  private readonly chatState = inject(ChatStateService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly appRef = inject(ApplicationRef);
  readonly presenceService = inject(PresenceService);

  readonly isOpen = input(false);
  readonly openConversacionId = input<string | null>(null);
  readonly openBotContext = input<string | null>(null);
  readonly close = output<void>();
  readonly unreadCountChange = output<number>();

  readonly conversaciones = signal<Conversacion[]>([]);
  readonly activeConversacion = signal<Conversacion | null>(null);
  readonly loadingConversaciones = signal(false);
  readonly searchOpen = signal(false);
  readonly jumpTarget = signal<string | null>(null);

  readonly currentUserId = computed(() => this.authService.currentUser()?.id ?? '');

  readonly peerName = computed(() => {
    const conv = this.activeConversacion();
    if (!conv) return '';
    if (conv.bot_context) {
      return this.getBotDisplayName(conv.bot_context);
    }
    const userId = this.currentUserId();
    return conv.participante_1 === userId
      ? conv.participante_2_nombre
      : conv.participante_1_nombre;
  });

  readonly totalUnread = computed(() =>
    this.conversaciones().reduce((sum, c) => sum + c.mensajes_sin_leer, 0)
  );

  readonly peerId = computed(() => {
    const conv = this.activeConversacion();
    if (!conv) return '';
    const userId = this.currentUserId();
    return conv.participante_1 === userId ? conv.participante_2 : conv.participante_1;
  });

  readonly peerStatus = computed(() =>
    this.presenceService.getStatus(this.peerId())
  );

  private readonly destroyRef = inject(DestroyRef);

  constructor() {
    // Optimistic update: reflect new message in the list immediately from the WS
    // payload so the preview and timestamp update without waiting for the REST call.
    this.chatSocket.newMessage$.pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(msg => {
      this.conversaciones.update(convs =>
        convs.map(c => c.id === msg.conversacion
          ? { ...c, ultimo_mensaje_contenido: msg.contenido, ultimo_mensaje_at: msg.created_at,
              mensajes_sin_leer: this.activeConversacion()?.id === msg.conversacion
                ? c.mensajes_sin_leer
                : c.mensajes_sin_leer + 1 }
          : c
        )
      );
    });

    // Debounced REST refresh to sync server-side fields (read counts, etc.)
    this.chatSocket.newMessage$.pipe(
      debounceTime(300),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(() => this.refreshConversaciones());

    // Emit unread count whenever it changes so the FAB badge stays in sync
    toObservable(this.totalUnread).pipe(
      distinctUntilChanged(),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(count => this.unreadCountChange.emit(count));

    // When a chat notification "Ver" is clicked, openConversacionId is set.
    // Find the conversation in the loaded list and open it directly.
    // markForCheck() is required because toObservable() fires its effect AFTER
    // the view renders, so the signal update alone won't schedule another CD pass.
    // When openBot() is called via ChatStateService, create/open the bot conversation
    toObservable(this.openBotContext).pipe(
      filter((ctx): ctx is string => ctx !== null),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(ctx => {
      this.openBotConversation(ctx);
      this.chatState.requestedBotContext.set(null);
    });

    toObservable(this.openConversacionId).pipe(
      filter((id): id is string => id !== null),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(id => {
      const conv = this.conversaciones().find(c => c.id === id);
      if (conv) {
        this.activeConversacion.set(conv);
        this.cdr.markForCheck();
        this.appRef.tick();
      } else {
        // Conversation not loaded yet — refresh list then open
        this.chatService.obtenerConversaciones().subscribe({
          next: convs => {
            this.conversaciones.set(convs);
            const found = convs.find(c => c.id === id);
            if (found) this.activeConversacion.set(found);
            this.cdr.markForCheck();
            this.appRef.tick();
          },
        });
      }
    });
  }

  ngOnInit(): void {
    this.loadConversaciones();
    if (this.authService.getAccessToken()) {
      this.chatSocket.connect();
      this.presenceService.start();
    }
  }

  ngOnDestroy(): void {
    this.chatSocket.disconnect();
  }

  loadConversaciones(): void {
    this.loadingConversaciones.set(true);
    this.chatService.obtenerConversaciones().subscribe({
      next: (convs) => {
        this.conversaciones.set(convs);
        this.loadingConversaciones.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.loadingConversaciones.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  refreshConversaciones(): void {
    this.chatService.obtenerConversaciones().subscribe({
      next: (convs) => {
        this.conversaciones.set(convs);
        this.cdr.markForCheck();
        this.appRef.tick();
      },
    });
  }

  openConversacion(conv: Conversacion): void {
    this.activeConversacion.set(conv);
  }

  backToList(): void {
    this.activeConversacion.set(null);
    this.searchOpen.set(false);
    this.jumpTarget.set(null);
    // Delay to let WS markRead operations complete before refreshing unread counts
    setTimeout(() => this.refreshConversaciones(), 600);
  }

  toggleSearch(): void {
    this.searchOpen.update(v => !v);
  }

  onJumpToMessage(mensajeId: string): void {
    this.searchOpen.set(false);
    this.jumpTarget.set(mensajeId);
  }

  buscarYCrearConversacion(destinatarioId: string): void {
    this.chatService.crearConversacion(destinatarioId).subscribe({
      next: (conv) => {
        this.activeConversacion.set(conv);
        this.cdr.markForCheck();
        this.refreshConversaciones();
      },
    });
  }

  private openBotConversation(context: string): void {
    this.chatService.crearConversacionBot(context).subscribe({
      next: (conv) => {
        const existing = this.conversaciones().find(c => c.id === conv.id);
        if (!existing) {
          this.conversaciones.update(list => [conv, ...list]);
        }
        this.activeConversacion.set(conv);
        this.cdr.markForCheck();
        this.appRef.tick();
      },
      error: (err) => {
        console.error('Error creating bot conversation:', err);
      },
    });
  }

  private getBotDisplayName(context: string): string {
    const names: Record<string, string> = {
      dashboard: 'CFO Virtual',
      proyectos: 'Asistente de Proyectos',
    };
    return names[context] ?? 'Asistente IA';
  }
}
