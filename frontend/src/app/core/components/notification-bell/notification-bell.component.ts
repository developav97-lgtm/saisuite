import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  TemplateRef,
  ViewContainerRef,
  effect,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatBadgeModule } from '@angular/material/badge';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Overlay, OverlayModule, OverlayRef } from '@angular/cdk/overlay';
import { TemplatePortal } from '@angular/cdk/portal';

import { NotificacionesService } from '../../services/notificaciones.service';
import { NotificationSocketService } from '../../services/notification-socket.service';
import { Notificacion, NotificacionGrupo, NotificacionItem } from '../../../shared/models/notificacion.model';

const TIPO_ICONS: Record<string, string> = {
  comentario:           'comment',
  mencion:              'alternate_email',
  aprobacion:           'task_alt',
  aprobacion_resultado: 'check_circle',
  asignacion:           'person_add',
  cambio_estado:        'sync',
  vencimiento:          'schedule',
  sistema:              'info',
  chat:                 'message',
  recordatorio:         'alarm',
};

// Opciones de snooze y remind-me en minutos
export const SNOOZE_OPTIONS = [
  { label: '30 minutos', minutos: 30 },
  { label: '1 hora',     minutos: 60 },
  { label: '3 horas',    minutos: 180 },
  { label: 'Mañana',     minutos: 1440 },
];

@Component({
  selector: 'app-notification-bell',
  standalone: true,
  imports: [
    RouterLink,
    OverlayModule,
    MatIconModule,
    MatButtonModule,
    MatBadgeModule,
    MatMenuModule,
    MatDividerModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
  ],
  templateUrl: './notification-bell.component.html',
  styleUrl: './notification-bell.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotificationBellComponent implements OnDestroy {
  private readonly svc             = inject(NotificacionesService);
  private readonly router          = inject(Router);
  private readonly socketService   = inject(NotificationSocketService);
  private readonly overlay         = inject(Overlay);
  private readonly viewContainerRef = inject(ViewContainerRef);

  sinLeer        = signal(0);
  items          = signal<NotificacionItem[]>([]);
  loading        = signal(false);
  // ID del item con panel de acciones expandido (snooze/remind-me)
  accionesId     = signal<string | null>(null);

  readonly snoozeOpts = SNOOZE_OPTIONS;

  // Referencia al template del panel de acciones
  readonly accionesTemplate = viewChild.required<TemplateRef<unknown>>('accionesPanel');

  // Overlay ref para el panel de acciones
  private _accionesOverlayRef: OverlayRef | null = null;
  private _docClickListener: ((e: MouseEvent) => void) | null = null;

  constructor() {
    // Sync badge count from WebSocket unread_count signal
    effect(() => {
      const wsCount = this.socketService.unreadCount();
      this.sinLeer.set(wsCount);
    });
  }

  ngOnDestroy(): void {
    this._cerrarAccionesPanel();
  }

  onMenuOpened(): void {
    this.loading.set(true);
    this._cerrarAccionesPanel();
    this.accionesId.set(null);
    this.svc.listarAgrupadas().subscribe({
      next: r  => { this.items.set(r); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  onMenuClosed(): void {
    this._cerrarAccionesPanel();
    this.accionesId.set(null);
  }

  // ── Navegar / marcar leída ─────────────────────────────────────────────────

  onIndividualClick(n: Notificacion): void {
    if (!n.leida) {
      this.svc.marcarLeida(n.id).subscribe({
        next: () => {
          this._quitarIndividual(n.id);
          this.sinLeer.update(c => Math.max(0, c - 1));
        },
      });
    }
    const url = n.ancla ? `${n.url_accion}${n.ancla}` : n.url_accion;
    if (url?.startsWith('/')) this.router.navigateByUrl(url);
  }

  onGrupoClick(g: NotificacionGrupo): void {
    this.svc.marcarGrupoLeidas(g.notificaciones_ids).subscribe({
      next: ({ count }) => {
        this._quitarGrupo(g.id);
        this.sinLeer.update(c => Math.max(0, c - count));
      },
    });
    const url = g.ancla ? `${g.url_accion}${g.ancla}` : g.url_accion;
    if (url?.startsWith('/')) this.router.navigateByUrl(url);
  }

  marcarTodasLeidas(): void {
    this.svc.marcarTodasLeidas().subscribe({
      next: () => {
        this.sinLeer.set(0);
        this.items.set([]);
      },
    });
  }

  // ── Panel de acciones (snooze / remind-me) ─────────────────────────────────

  toggleAcciones(event: Event, itemId: string): void {
    event.stopPropagation();

    // Si ya está abierto para el mismo item, cerrarlo
    if (this.accionesId() === itemId) {
      this._cerrarAccionesPanel();
      return;
    }

    // Cerrar cualquier panel previo
    this._cerrarAccionesPanel();

    const btn = event.currentTarget as HTMLElement;

    // Crear posicion estrategia: anclar debajo del boton, alineado a la derecha
    const positionStrategy = this.overlay
      .position()
      .flexibleConnectedTo(btn)
      .withPositions([
        {
          originX: 'end',
          originY: 'bottom',
          overlayX: 'end',
          overlayY: 'top',
          offsetY: 4,
        },
        {
          // Fallback: abrir hacia arriba si no hay espacio abajo
          originX: 'end',
          originY: 'top',
          overlayX: 'end',
          overlayY: 'bottom',
          offsetY: -4,
        },
      ])
      .withPush(true)
      .withViewportMargin(8);

    this._accionesOverlayRef = this.overlay.create({
      positionStrategy,
      scrollStrategy: this.overlay.scrollStrategies.reposition(),
      hasBackdrop: false,
    });

    // Cerrar al hacer click fuera del panel usando listener en document
    // Se usa setTimeout para evitar que el click que abre el panel lo cierre inmediatamente
    setTimeout(() => {
      this._docClickListener = (e: MouseEvent) => {
        const target = e.target as HTMLElement;
        const panel = this._accionesOverlayRef?.overlayElement;
        if (panel && !panel.contains(target)) {
          this._cerrarAccionesPanel();
        }
      };
      document.addEventListener('click', this._docClickListener, { capture: true });
    }, 0);

    // Renderizar el template en el overlay
    const portal = new TemplatePortal(
      this.accionesTemplate(),
      this.viewContainerRef,
      { $implicit: itemId },
    );

    this._accionesOverlayRef.attach(portal);
    this.accionesId.set(itemId);
  }

  private _cerrarAccionesPanel(): void {
    if (this._docClickListener) {
      document.removeEventListener('click', this._docClickListener, { capture: true });
      this._docClickListener = null;
    }
    if (this._accionesOverlayRef) {
      this._accionesOverlayRef.detach();
      this._accionesOverlayRef.dispose();
      this._accionesOverlayRef = null;
    }
    this.accionesId.set(null);
  }

  onSnooze(event: Event, notifId: string, minutos: number): void {
    event.stopPropagation();
    this.svc.snooze(notifId, minutos).subscribe({
      next: () => {
        this._quitarIndividual(notifId);
        this.sinLeer.update(c => Math.max(0, c - 1));
        this._cerrarAccionesPanel();
      },
    });
  }

  onSnoozeGrupo(event: Event, g: NotificacionGrupo, minutos: number): void {
    event.stopPropagation();
    // Snooze a cada notificación del grupo
    let pendientes = g.notificaciones_ids.length;
    g.notificaciones_ids.forEach(id => {
      this.svc.snooze(id, minutos).subscribe({
        next: () => {
          pendientes--;
          if (pendientes === 0) {
            this._quitarGrupo(g.id);
            this.sinLeer.update(c => Math.max(0, c - g.cantidad));
            this._cerrarAccionesPanel();
          }
        },
      });
    });
  }

  onRemindMe(event: Event, notifId: string, minutos: number): void {
    event.stopPropagation();
    this.svc.remindMe(notifId, minutos).subscribe({
      next: () => {
        this._quitarIndividual(notifId);
        this.sinLeer.update(c => Math.max(0, c - 1));
        this._cerrarAccionesPanel();
      },
    });
  }

  // ── Helpers ─────────────────────────────────────────────────────────────────

  getTipoIcon(tipo: string): string {
    return TIPO_ICONS[tipo] ?? 'notifications';
  }

  formatTiempo(fecha: string): string {
    const diff  = Date.now() - new Date(fecha).getTime();
    const min   = Math.floor(diff / 60_000);
    const horas = Math.floor(diff / 3_600_000);
    const dias  = Math.floor(diff / 86_400_000);
    if (min < 1)    return 'Ahora';
    if (min < 60)   return `Hace ${min}m`;
    if (horas < 24) return `Hace ${horas}h`;
    if (dias < 7)   return `Hace ${dias}d`;
    return new Date(fecha).toLocaleDateString('es-CO');
  }

  private _quitarIndividual(id: string): void {
    this.items.update(list =>
      list.filter(item =>
        item.tipo === 'grupo' || item.notificacion.id !== id,
      ),
    );
  }

  private _quitarGrupo(grupoId: string): void {
    this.items.update(list =>
      list.filter(item =>
        item.tipo === 'individual' || item.id !== grupoId,
      ),
    );
  }
}
