/**
 * QuickAccessDialogComponent
 * Dialog overlay con navegación interna completa.
 * - Registra rutas en QuickAccessNavigatorService al abrirse.
 * - Mantiene un historial para poder navegar "atrás" dentro del dialog.
 * - Al cerrar, desregistra el interceptor y la app vuelve a funcionar normal.
 */
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  Type,
  inject,
  signal,
} from '@angular/core';
import { NgComponentOutlet } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subscription } from 'rxjs';
import {
  QuickAccessNavigatorService,
  QuickAccessRoute,
} from '../../services/quick-access-navigator.service';

export interface QuickAccessDialogData {
  title: string;
  component: Type<unknown>;
  /** Rutas que el dialog puede manejar internamente */
  routes: QuickAccessRoute[];
}

@Component({
  selector: 'app-quick-access-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    NgComponentOutlet,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
  ],
  template: `
    <div class="qa-header" mat-dialog-title>
      <div class="qa-header-left">
        @if (canGoBack()) {
          <button mat-icon-button (click)="goBack()" matTooltip="Volver" class="qa-back">
            <mat-icon>arrow_back</mat-icon>
          </button>
        }
        <span class="qa-title">{{ currentTitle() }}</span>
      </div>
      <button mat-icon-button mat-dialog-close matTooltip="Cerrar" class="qa-close">
        <mat-icon>close</mat-icon>
      </button>
    </div>
    <div class="qa-body">
      <ng-container [ngComponentOutlet]="currentComponent()" />
    </div>
  `,
  styles: [`
    :host { display: flex; flex-direction: column; height: 100%; overflow: hidden; }

    .qa-header {
      display: flex !important;
      align-items: center;
      justify-content: space-between;
      padding: 0.5rem 1rem 0.5rem 0.5rem !important;
      border-bottom: 1px solid var(--sc-surface-border);
      background: var(--sc-surface-card);
      flex-shrink: 0;
      margin: 0 !important;
      gap: 0.5rem;
    }

    .qa-header-left {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      min-width: 0;
    }

    .qa-title {
      font-size: 1rem;
      font-weight: 600;
      color: var(--sc-text-color);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .qa-close { opacity: 0.6; flex-shrink: 0; }
    .qa-close:hover { opacity: 1; }

    .qa-body {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      background: var(--sc-surface-ground);
    }
  `],
})
export class QuickAccessDialogComponent implements OnInit, OnDestroy {
  readonly data      = inject<QuickAccessDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<QuickAccessDialogComponent>);
  private readonly navigator = inject(QuickAccessNavigatorService);
  private readonly cdr       = inject(ChangeDetectorRef);

  // Historial de navegación interna: [ { title, component } ]
  private history: { title: string; component: Type<unknown> }[] = [];

  readonly currentComponent = signal<Type<unknown> | null>(null);
  readonly currentTitle     = signal('');
  readonly canGoBack        = signal(false);

  private navSub?: Subscription;

  ngOnInit(): void {
    // Estado inicial
    this.history = [{ title: this.data.title, component: this.data.component }];
    this.syncSignals();

    // Registrar rutas y activar interceptor
    this.navigator.register(this.data.routes);

    // Escuchar navegaciones interceptadas
    this.navSub = this.navigator.intercepted$.subscribe(url => {
      this.handleInternalNavigation(url);
    });
  }

  ngOnDestroy(): void {
    this.navigator.unregister();
    this.navSub?.unsubscribe();
  }

  goBack(): void {
    if (this.history.length > 1) {
      this.history.pop();
      this.syncSignals();
    }
  }

  private async handleInternalNavigation(url: string): Promise<void> {
    const component = await this.navigator.resolveComponent(url);
    if (!component) return;

    // Infere título desde la URL
    const title = this.titleFromUrl(url);
    this.history.push({ title, component });
    this.syncSignals();
  }

  private syncSignals(): void {
    const current = this.history[this.history.length - 1];
    this.currentComponent.set(current.component);
    this.currentTitle.set(current.title);
    this.canGoBack.set(this.history.length > 1);
    this.cdr.markForCheck();
  }

  private titleFromUrl(url: string): string {
    const base = this.data.title;
    if (url.includes('/nuevo'))   return `${base} — Nuevo`;
    if (url.includes('/editar'))  return `${base} — Editar`;
    if (url.includes('/nuevo') || url.endsWith('/nuevo')) return `${base} — Nuevo`;
    return base;
  }
}
