import {
  ChangeDetectionStrategy, Component, DestroyRef, inject, input, output,
  signal,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject, debounceTime, distinctUntilChanged, filter, switchMap } from 'rxjs';
import { ChatService } from '../../services/chat.service';
import { Mensaje } from '../../models/chat.models';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-chat-search',
  imports: [
    MatIconModule, MatButtonModule, MatFormFieldModule,
    MatInputModule, MatProgressBarModule, FormsModule, DatePipe,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="chat-search">
      <div class="chat-search__input-row">
        <mat-form-field appearance="outline" class="chat-search__field">
          <mat-icon matPrefix>search</mat-icon>
          <input matInput
                 placeholder="Buscar en la conversación..."
                 [ngModel]="query()"
                 (ngModelChange)="onQueryChange($event)"
                 (keydown.escape)="close.emit()" />
          @if (query()) {
            <button matSuffix mat-icon-button (click)="clearQuery()">
              <mat-icon>close</mat-icon>
            </button>
          }
        </mat-form-field>
      </div>

      @if (loading()) {
        <mat-progress-bar mode="indeterminate" />
      }

      @if (results().length > 0) {
        <div class="chat-search__results">
          <p class="chat-search__count">{{ results().length }} resultado(s) para "{{ lastQuery() }}"</p>
          @for (msg of results(); track msg.id) {
            <button class="chat-search__result" (click)="jumpToMessage.emit(msg.id)">
              <div class="chat-search__result-meta">
                <span class="chat-search__result-author">{{ msg.remitente_nombre }}</span>
                <span class="chat-search__result-time">{{ msg.created_at | date:'short' }}</span>
              </div>
              <div class="chat-search__result-text"
                   [innerHTML]="highlight(msg.contenido)">
              </div>
            </button>
          }
        </div>
      } @else if (lastQuery() && !loading()) {
        <div class="chat-search__empty">
          <mat-icon>search_off</mat-icon>
          <p>Sin resultados para "{{ lastQuery() }}"</p>
        </div>
      }
    </div>
  `,
  styles: [`
    .chat-search {
      display: flex;
      flex-direction: column;
      background: var(--sc-surface-card, #fff);
      border-bottom: 2px solid var(--sc-primary, #1565c0);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
      z-index: 1;
    }

    .chat-search__input-row {
      padding: 8px 12px 0;
    }

    .chat-search__field {
      width: 100%;
    }

    .chat-search__results {
      max-height: 240px;
      overflow-y: auto;
      padding: 4px 0 8px;
    }

    .chat-search__count {
      padding: 0 16px 4px;
      font-size: 0.75rem;
      color: var(--sc-text-muted, #718096);
      margin: 0;
    }

    .chat-search__result {
      display: flex;
      flex-direction: column;
      gap: 2px;
      width: 100%;
      text-align: left;
      padding: 8px 16px;
      border: none;
      background: transparent;
      cursor: pointer;
      border-bottom: 1px solid var(--sc-surface-border, #e2e8f0);

      &:hover {
        background: var(--sc-surface-hover, #f0f2f5);
      }

      &:last-child { border-bottom: none; }
    }

    .chat-search__result-meta {
      display: flex;
      justify-content: space-between;
      font-size: 0.75rem;
    }

    .chat-search__result-author {
      font-weight: 600;
      color: var(--sc-primary, #1565c0);
    }

    .chat-search__result-time {
      color: var(--sc-text-muted, #718096);
    }

    .chat-search__result-text {
      font-size: 0.85rem;
      color: var(--sc-text-color, #1a202c);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;

      ::ng-deep mark {
        background: #fff176;
        color: inherit;
        border-radius: 2px;
        padding: 0 1px;
      }
    }

    .chat-search__empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 16px;
      color: var(--sc-text-muted, #718096);
      font-size: 0.85rem;

      mat-icon { font-size: 32px; width: 32px; height: 32px; }
    }
  `],
})
export class ChatSearchComponent {
  private readonly chatService = inject(ChatService);
  private readonly destroyRef = inject(DestroyRef);

  readonly conversacionId = input.required<string>();
  readonly close = output<void>();
  readonly jumpToMessage = output<string>();

  readonly query = signal('');
  readonly results = signal<Mensaje[]>([]);
  readonly loading = signal(false);
  readonly lastQuery = signal('');

  private readonly querySubject = new Subject<string>();

  constructor() {
    this.querySubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      filter(q => q.length >= 2),
      switchMap(q => {
        this.loading.set(true);
        return this.chatService.buscarMensajes(this.conversacionId(), q);
      }),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (res) => {
        this.results.set(res.results);
        this.lastQuery.set(res.query);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  onQueryChange(value: string): void {
    this.query.set(value);
    if (!value.trim()) {
      this.results.set([]);
      this.lastQuery.set('');
      this.loading.set(false);
    } else {
      this.querySubject.next(value.trim());
    }
  }

  clearQuery(): void {
    this.query.set('');
    this.results.set([]);
    this.lastQuery.set('');
  }

  highlight(text: string): string {
    const q = this.lastQuery();
    if (!q) return text;
    const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return text.replace(new RegExp(escaped, 'gi'), match => `<mark>${match}</mark>`);
  }
}
