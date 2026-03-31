import { Injectable, signal } from '@angular/core';

/**
 * Shared service to open the chat panel from anywhere in the app
 * (e.g., notification bell) without going through component outputs.
 */
@Injectable({ providedIn: 'root' })
export class ChatStateService {
  readonly isOpen = signal(false);
  readonly requestedConversacionId = signal<string | null>(null);

  open(conversacionId?: string): void {
    if (conversacionId) this.requestedConversacionId.set(conversacionId);
    this.isOpen.set(true);
  }

  close(): void {
    this.isOpen.set(false);
    this.requestedConversacionId.set(null);
  }
}
