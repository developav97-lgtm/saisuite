import { ChangeDetectionStrategy, Component, input, output, computed } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatBadgeModule } from '@angular/material/badge';

@Component({
  selector: 'app-chat-fab',
  imports: [MatIconModule, MatButtonModule, MatBadgeModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button
      mat-fab
      color="primary"
      class="chat-fab"
      [matBadge]="badgeText()"
      [matBadgeHidden]="unreadCount() === 0"
      matBadgeColor="warn"
      (click)="toggle.emit()"
      aria-label="Abrir chat">
      <mat-icon>{{ isOpen() ? 'close' : 'chat' }}</mat-icon>
    </button>
  `,
  styles: [`
    :host {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 1000;
      transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    :host(.fab--panel-open) {
      right: 444px;
    }

    .chat-fab {
      transition: transform 0.2s ease;

      &:hover {
        transform: scale(1.05);
      }
    }

    @media (max-width: 480px) {
      :host(.fab--panel-open) {
        display: none;
      }
    }
  `],
  host: {
    '[class.fab--panel-open]': 'isOpen()',
  },
})
export class ChatFabComponent {
  readonly isOpen = input(false);
  readonly unreadCount = input(0);
  readonly toggle = output<void>();

  readonly badgeText = computed(() => {
    const count = this.unreadCount();
    return count > 99 ? '99+' : String(count);
  });
}
