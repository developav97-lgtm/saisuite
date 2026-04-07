import { ChangeDetectionStrategy, Component, inject, input, output, signal } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDividerModule } from '@angular/material/divider';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { Conversacion, AutocompleteUsuario } from '../../models/chat.models';
import { ChatService } from '../../services/chat.service';
import { PresenceService } from '../../services/presence.service';

@Component({
  selector: 'app-chat-list',
  imports: [
    MatIconModule, MatFormFieldModule, MatInputModule,
    MatProgressBarModule, MatDividerModule, FormsModule, DatePipe,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (loading()) {
      <mat-progress-bar mode="indeterminate" />
    }

    <div class="chat-list__search">
      <mat-form-field appearance="outline" class="chat-list__search-field">
        <mat-icon matPrefix>search</mat-icon>
        <input matInput
               placeholder="Buscar usuario..."
               [ngModel]="searchQuery()"
               (ngModelChange)="onSearch($event)" />
      </mat-form-field>
    </div>

    @if (searchResults().length > 0) {
      <div class="chat-list__results">
        <div class="chat-list__results-label">Usuarios</div>
        @for (user of searchResults(); track user.id) {
          <button class="chat-list__item" (click)="buscarUsuario.emit(user.id)">
            <div class="chat-list__avatar-wrap">
              <mat-icon class="chat-list__avatar">account_circle</mat-icon>
              <span class="chat-list__presence-dot"
                    [class.chat-list__presence-dot--online]="presenceService.getStatus(user.id) === 'online'">
              </span>
            </div>
            <div class="chat-list__info">
              <div class="chat-list__row-top">
                <span class="chat-list__name">{{ user.nombre }}</span>
              </div>
              <div class="chat-list__row-bottom">
                <span class="chat-list__preview">{{ user.email }}</span>
              </div>
            </div>
          </button>
        }
        <mat-divider class="chat-list__divider" />
      </div>
    }

    <div class="chat-list__conversations">
      @for (conv of conversaciones(); track conv.id) {
        <button class="chat-list__item" (click)="selectConversacion.emit(conv)">
          <div class="chat-list__avatar-wrap">
            @if (conv.bot_context) {
              <mat-icon class="chat-list__avatar chat-list__avatar--bot">smart_toy</mat-icon>
            } @else {
              <mat-icon class="chat-list__avatar">account_circle</mat-icon>
              <span class="chat-list__presence-dot"
                    [class.chat-list__presence-dot--online]="presenceService.getStatus(getPeerId(conv)) === 'online'">
              </span>
            }
          </div>
          <div class="chat-list__info">
            <div class="chat-list__row-top">
              <span class="chat-list__name">{{ conv.bot_context ? getBotName(conv.bot_context) : getPeerName(conv) }}</span>
              <span class="chat-list__time">
                @if (conv.ultimo_mensaje_at) {
                  {{ conv.ultimo_mensaje_at | date:'shortTime' }}
                }
              </span>
            </div>
            <div class="chat-list__row-bottom">
              <span class="chat-list__preview">{{ conv.ultimo_mensaje_contenido || 'Sin mensajes' }}</span>
              @if (conv.mensajes_sin_leer > 0) {
                <span class="chat-list__badge">{{ conv.mensajes_sin_leer }}</span>
              }
            </div>
          </div>
        </button>
      } @empty {
        @if (!loading()) {
          <div class="chat-list__empty">
            <mat-icon>chat_bubble_outline</mat-icon>
            <p>No hay conversaciones</p>
            <p class="chat-list__empty-hint">Busca un usuario para iniciar</p>
          </div>
        }
      }
    </div>
  `,
  styles: [`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
    }

    .chat-list__search {
      padding: 12px 16px 0;
    }

    .chat-list__search-field {
      width: 100%;
    }

    .chat-list__results {
      padding: 0 8px;
    }

    .chat-list__results-label {
      padding: 4px 16px;
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--sc-text-muted, #718096);
      text-transform: uppercase;
    }

    .chat-list__divider {
      margin: 4px 0 8px;
    }

    .chat-list__conversations {
      flex: 1;
      overflow-y: auto;
      padding: 4px 8px 8px;
    }

    .chat-list__item {
      display: flex;
      align-items: center;
      gap: 12px;
      width: 100%;
      padding: 10px 12px;
      border: none;
      background: none;
      cursor: pointer;
      text-align: left;
      border-radius: 10px;
      transition: background 0.15s;
      box-sizing: border-box;

      &:hover {
        background: var(--sc-primary-light, #e8f0fe);
      }
    }

    .chat-list__avatar-wrap {
      position: relative;
      width: 40px;
      height: 40px;
      flex-shrink: 0;
    }

    .chat-list__avatar {
      font-size: 40px;
      width: 40px;
      height: 40px;
      color: var(--sc-text-muted, #718096);

      &--bot {
        color: var(--sc-primary, #1565c0);
      }
    }

    .chat-list__presence-dot {
      position: absolute;
      top: -1px;
      right: -1px;
      width: 11px;
      height: 11px;
      border-radius: 50%;
      background: var(--sc-surface-border, #cbd5e0);
      border: 2px solid var(--sc-surface-card, #fff);

      &--online {
        background: #22c55e;
      }
    }

    .chat-list__info {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .chat-list__row-top {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .chat-list__name {
      flex: 1;
      font-weight: 600;
      font-size: 0.9rem;
      color: var(--sc-text-color, #1a202c);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .chat-list__time {
      flex-shrink: 0;
      font-size: 0.72rem;
      color: var(--sc-text-muted, #718096);
    }

    .chat-list__row-bottom {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .chat-list__preview {
      flex: 1;
      font-size: 0.82rem;
      color: var(--sc-text-muted, #718096);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .chat-list__badge {
      flex-shrink: 0;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 20px;
      height: 20px;
      padding: 0 6px;
      border-radius: 10px;
      background: var(--sc-primary, #1565c0);
      color: white;
      font-size: 0.7rem;
      font-weight: 600;
    }

    .chat-list__empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 48px 24px;
      text-align: center;

      mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        color: var(--sc-text-muted, #718096);
        margin-bottom: 12px;
      }

      p {
        margin: 0;
        color: var(--sc-text-muted, #718096);
      }
    }

    .chat-list__empty-hint {
      font-size: 0.85rem;
      margin-top: 4px !important;
    }
  `],
})
export class ChatListComponent {
  private readonly chatService = inject(ChatService);
  readonly presenceService = inject(PresenceService);

  readonly conversaciones = input<Conversacion[]>([]);
  readonly currentUserId = input('');
  readonly loading = input(false);
  readonly selectConversacion = output<Conversacion>();
  readonly buscarUsuario = output<string>();

  readonly searchQuery = signal('');
  readonly searchResults = signal<AutocompleteUsuario[]>([]);

  private searchTimeout: ReturnType<typeof setTimeout> | null = null;

  getPeerName(conv: Conversacion): string {
    return conv.participante_1 === this.currentUserId()
      ? conv.participante_2_nombre
      : conv.participante_1_nombre;
  }

  getPeerId(conv: Conversacion): string {
    return conv.participante_1 === this.currentUserId()
      ? conv.participante_2
      : conv.participante_1;
  }

  getBotName(context: string): string {
    const names: Record<string, string> = {
      dashboard: 'CFO Virtual',
      proyectos: 'Asistente de Proyectos',
    };
    return names[context] ?? 'Asistente IA';
  }

  onSearch(query: string): void {
    this.searchQuery.set(query);

    if (this.searchTimeout) clearTimeout(this.searchTimeout);

    if (query.length < 2) {
      this.searchResults.set([]);
      return;
    }

    this.searchTimeout = setTimeout(() => {
      this.chatService.autocompleteUsuarios(query).subscribe({
        next: (results) => this.searchResults.set(results),
      });
    }, 300);
  }
}
