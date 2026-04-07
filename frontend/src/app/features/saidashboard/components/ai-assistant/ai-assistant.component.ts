import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ChatStateService } from '../../../../core/services/chat-state.service';

interface AssistantMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AssistantResponse {
  response: string;
}

const QUICK_ACTIONS = [
  { label: 'Como esta mi liquidez?', icon: 'account_balance' },
  { label: 'Riesgo de endeudamiento?', icon: 'warning' },
  { label: 'Resumen financiero del mes', icon: 'summarize' },
  { label: 'Proyeccion de ingresos', icon: 'trending_up' },
];

@Component({
  selector: 'app-ai-assistant',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatTooltipModule,
    MatProgressBarModule,
  ],
  templateUrl: './ai-assistant.component.html',
  styleUrl: './ai-assistant.component.scss',
})
export class AiAssistantComponent {
  private readonly http = inject(HttpClient);
  private readonly destroyRef = inject(DestroyRef);
  private readonly chatState = inject(ChatStateService);

  readonly messagesContainer = viewChild<ElementRef<HTMLElement>>('messagesContainer');

  readonly isOpen = signal(false);
  readonly messages = signal<AssistantMessage[]>([]);
  readonly inputText = signal('');
  readonly loading = signal(false);
  readonly quickActions = QUICK_ACTIONS;

  toggle(): void {
    this.isOpen.update(v => !v);
  }

  sendMessage(text?: string): void {
    const message = text ?? this.inputText().trim();
    if (!message) return;

    // Add user message
    this.messages.update(msgs => [
      ...msgs,
      { role: 'user', content: message, timestamp: new Date() },
    ]);
    this.inputText.set('');
    this.loading.set(true);
    this.scrollToBottom();

    // Call CFO Virtual API
    this.http.post<AssistantResponse>('/api/v1/dashboard/cfo-virtual/', { question: message })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.messages.update(msgs => [
            ...msgs,
            { role: 'assistant', content: res.response, timestamp: new Date() },
          ]);
          this.loading.set(false);
          this.scrollToBottom();
        },
        error: () => {
          this.messages.update(msgs => [
            ...msgs,
            {
              role: 'assistant',
              content: 'Lo siento, no pude procesar tu consulta en este momento. Intenta de nuevo mas tarde.',
              timestamp: new Date(),
            },
          ]);
          this.loading.set(false);
          this.scrollToBottom();
        },
      });
  }

  openFullChat(): void {
    this.chatState.openBot('dashboard');
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      const container = this.messagesContainer()?.nativeElement;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }, 50);
  }
}
