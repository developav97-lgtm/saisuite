import {
  ChangeDetectionStrategy, Component, inject, input, output,
  signal, computed, ElementRef, viewChild, AfterViewInit,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormsModule } from '@angular/forms';
import {
  AutocompleteDropdownComponent,
  AutocompleteItem,
} from '../autocomplete-dropdown/autocomplete-dropdown.component';
import { EmojiPickerComponent } from '../emoji-picker/emoji-picker.component';
import { ChatService } from '../../services/chat.service';
import { AutocompleteEntidad, AutocompleteUsuario } from '../../models/chat.models';

@Component({
  selector: 'app-message-input',
  imports: [
    MatIconModule, MatButtonModule, MatTooltipModule,
    FormsModule, AutocompleteDropdownComponent, EmojiPickerComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="msg-input" (keydown)="onKeydown($event)">
      @if (showAutocomplete()) {
        <app-autocomplete-dropdown
          [items]="autocompleteItems()"
          [activeIndex]="autocompleteIndex()"
          [loading]="autocompleteLoading()"
          (select)="onAutocompleteSelect($event)" />
      }
      @if (showEmojiPicker()) {
        <div class="msg-input__emoji-backdrop" (click)="showEmojiPicker.set(false)"></div>
        <app-emoji-picker
          class="msg-input__emoji-dropdown"
          (emojiSelect)="onEmojiSelect($event)" />
      }
      <textarea
        #textArea
        class="msg-input__textarea"
        placeholder="Escribe un mensaje..."
        [ngModel]="text()"
        (ngModelChange)="onTextChange($event)"
        (keydown.enter)="onEnter($event)"
        rows="1">
      </textarea>
      <button mat-icon-button
              (click)="toggleEmojiPicker()"
              matTooltip="Emojis">
        <mat-icon>mood</mat-icon>
      </button>
      <button mat-icon-button
              color="primary"
              [disabled]="!canSend()"
              (click)="onSend()"
              matTooltip="Enviar">
        <mat-icon>send</mat-icon>
      </button>
    </div>
  `,
  styles: [`
    :host {
      display: flex;
      flex: 1;
      min-width: 0;
    }

    .msg-input {
      position: relative;
      display: flex;
      align-items: flex-end;
      gap: 4px;
      flex: 1;
      min-width: 0;
    }

    .msg-input__textarea {
      flex: 1;
      min-width: 0;
      resize: none;
      border: 1.5px solid var(--sc-surface-border, #e2e8f0);
      border-radius: 22px;
      padding: 9px 14px;
      font-family: inherit;
      font-size: 0.9rem;
      line-height: 1.5;
      background: var(--sc-surface-ground, rgba(255,255,255,0.08));
      color: var(--sc-text-color, #1a202c);
      outline: none;
      overflow-y: hidden;
      transition: border-color 0.15s, box-shadow 0.15s;
      min-height: 38px;
      max-height: 120px;
      box-sizing: border-box;

      &:focus {
        border-color: var(--sc-primary, #1565c0);
        box-shadow: 0 0 0 3px rgba(21, 101, 192, 0.12);
      }

      &::placeholder {
        color: var(--sc-text-muted, #718096);
      }
    }

    .msg-input__emoji-backdrop {
      position: fixed;
      inset: 0;
      z-index: 199;
    }

    .msg-input__emoji-dropdown {
      position: absolute;
      bottom: calc(100% + 6px);
      right: 44px;
      z-index: 200;
    }
  `],
})
export class MessageInputComponent implements AfterViewInit {
  private readonly chatService = inject(ChatService);
  private readonly textArea = viewChild<ElementRef>('textArea');

  ngAfterViewInit(): void {
    this.resetHeight();
  }

  readonly conversacionId = input.required<string>();
  readonly hasPendingAttachment = input(false);
  readonly sendMessage = output<string>();
  readonly typing = output<void>();

  readonly text = signal('');
  readonly showAutocomplete = signal(false);
  readonly autocompleteItems = signal<AutocompleteItem[]>([]);
  readonly autocompleteIndex = signal(0);
  readonly showEmojiPicker = signal(false);

  readonly canSend = computed(() =>
    this.text().trim().length > 0 || this.hasPendingAttachment()
  );
  readonly autocompleteLoading = signal(false);

  private triggerChar: '[' | '@' | null = null;
  private triggerStart = 0;
  private searchTimeout: ReturnType<typeof setTimeout> | null = null;
  private typingThrottle: ReturnType<typeof setTimeout> | null = null;

  toggleEmojiPicker(): void {
    this.showEmojiPicker.update(v => !v);
    if (this.showEmojiPicker()) {
      this.closeAutocomplete();
    }
  }

  onEmojiSelect(emoji: string): void {
    const el = this.textArea()?.nativeElement as HTMLTextAreaElement | undefined;
    const start = el?.selectionStart ?? this.text().length;
    const end = el?.selectionEnd ?? start;
    const current = this.text();
    const newText = current.slice(0, start) + emoji + current.slice(end);
    this.text.set(newText);
    this.autoResize();
    if (el) {
      setTimeout(() => {
        // Use emoji.length (UTF-16 units) to stay consistent with selectionStart/End
        const newPos = start + emoji.length;
        el.setSelectionRange(newPos, newPos);
        el.focus();
      });
    }
    // Keep picker open so the user can insert multiple emojis
  }

  onTextChange(value: string): void {
    this.text.set(value);
    this.autoResize();
    this.detectTrigger(value);
    this.emitTyping();
  }

  onEnter(event: Event): void {
    const ke = event as KeyboardEvent;
    if (this.showAutocomplete()) {
      ke.preventDefault();
      const items = this.autocompleteItems();
      const idx = this.autocompleteIndex();
      if (items[idx]) {
        this.onAutocompleteSelect(items[idx]);
      }
      return;
    }
    if (!ke.shiftKey && this.canSend()) {
      ke.preventDefault();
      this.onSend();
    }
  }

  onKeydown(event: KeyboardEvent): void {
    if (this.showEmojiPicker()) {
      if (event.key === 'Escape') {
        event.preventDefault();
        this.showEmojiPicker.set(false);
      }
      return;
    }
    if (!this.showAutocomplete()) return;

    const items = this.autocompleteItems();
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      this.autocompleteIndex.update(i => Math.min(i + 1, items.length - 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      this.autocompleteIndex.update(i => Math.max(i - 1, 0));
    } else if (event.key === 'Escape') {
      event.preventDefault();
      this.closeAutocomplete();
    }
  }

  onAutocompleteSelect(item: AutocompleteItem): void {
    const currentText = this.text();
    const before = currentText.substring(0, this.triggerStart);
    const after = currentText.substring(this.getCursorPosition());

    let replacement: string;
    if (item.kind === 'entidad') {
      replacement = `[${item.value.codigo}]`;
    } else {
      replacement = `@${item.value.nombre}`;
    }

    this.text.set(before + replacement + after);
    this.closeAutocomplete();
  }

  onSend(): void {
    if (!this.canSend()) return;
    const trimmed = this.text().trim();
    this.sendMessage.emit(trimmed);
    this.text.set('');
    this.closeAutocomplete();
    this.showEmojiPicker.set(false);
    this.resetHeight();
  }

  private detectTrigger(value: string): void {
    const pos = this.getCursorPosition();
    const charBefore = value[pos - 1];

    if (this.triggerChar) {
      const query = value.substring(this.triggerStart + 1, pos);
      if (query.length >= 1) {
        this.fetchAutocomplete(query);
      } else if (query.length === 0 || value[this.triggerStart] !== this.triggerChar) {
        this.closeAutocomplete();
      }
      return;
    }

    if (charBefore === '[') {
      this.triggerChar = '[';
      this.triggerStart = pos - 1;
      this.showAutocomplete.set(true);
      this.autocompleteItems.set([]);
      this.autocompleteIndex.set(0);
    } else if (charBefore === '@') {
      this.triggerChar = '@';
      this.triggerStart = pos - 1;
      this.showAutocomplete.set(true);
      this.autocompleteItems.set([]);
      this.autocompleteIndex.set(0);
    }
  }

  private fetchAutocomplete(query: string): void {
    if (this.searchTimeout) clearTimeout(this.searchTimeout);
    this.autocompleteLoading.set(true);

    this.searchTimeout = setTimeout(() => {
      if (this.triggerChar === '[') {
        this.chatService.autocompleteEntidades(query).subscribe({
          next: (results: AutocompleteEntidad[]) => {
            this.autocompleteItems.set(
              results.map(e => ({ kind: 'entidad' as const, value: e })),
            );
            this.autocompleteIndex.set(0);
            this.autocompleteLoading.set(false);
          },
          error: () => this.autocompleteLoading.set(false),
        });
      } else if (this.triggerChar === '@') {
        this.chatService.autocompleteUsuarios(query).subscribe({
          next: (results: AutocompleteUsuario[]) => {
            this.autocompleteItems.set(
              results.map(u => ({ kind: 'usuario' as const, value: u })),
            );
            this.autocompleteIndex.set(0);
            this.autocompleteLoading.set(false);
          },
          error: () => this.autocompleteLoading.set(false),
        });
      }
    }, 200);
  }

  private closeAutocomplete(): void {
    this.showAutocomplete.set(false);
    this.autocompleteItems.set([]);
    this.autocompleteIndex.set(0);
    this.autocompleteLoading.set(false);
    this.triggerChar = null;
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout);
      this.searchTimeout = null;
    }
  }

  private autoResize(): void {
    const el = this.textArea()?.nativeElement as HTMLTextAreaElement | undefined;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  }

  private resetHeight(): void {
    const el = this.textArea()?.nativeElement as HTMLTextAreaElement | undefined;
    if (!el) return;
    el.style.height = '38px';
  }

  private getCursorPosition(): number {
    const el = this.textArea()?.nativeElement as HTMLTextAreaElement | undefined;
    return el?.selectionStart ?? this.text().length;
  }

  private emitTyping(): void {
    if (this.typingThrottle) return;
    this.typing.emit();
    this.typingThrottle = setTimeout(() => {
      this.typingThrottle = null;
    }, 3000);
  }
}
