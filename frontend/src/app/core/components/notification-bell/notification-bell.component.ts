import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatBadgeModule } from '@angular/material/badge';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { interval } from 'rxjs';

import { NotificacionesService } from '../../services/notificaciones.service';
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
export class NotificationBellComponent implements OnInit {
  private readonly svc        = inject(NotificacionesService);
  private readonly router     = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  sinLeer        = signal(0);
  items          = signal<NotificacionItem[]>([]);
  loading        = signal(false);
  // ID del item con panel de acciones expandido (snooze/remind-me)
  accionesId     = signal<string | null>(null);

  readonly snoozeOpts = SNOOZE_OPTIONS;

  ngOnInit(): void {
    this.cargarConteo();
    interval(30_000)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.cargarConteo());
  }

  cargarConteo(): void {
    this.svc.contarSinLeer().subscribe({
      next: r  => this.sinLeer.set(r.count),
      error: () => { /* silencioso */ },
    });
  }

  onMenuOpened(): void {
    this.loading.set(true);
    this.accionesId.set(null);
    this.svc.listarAgrupadas().subscribe({
      next: r  => { this.items.set(r); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
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
    if (url) this.router.navigateByUrl(url);
  }

  onGrupoClick(g: NotificacionGrupo): void {
    this.svc.marcarGrupoLeidas(g.notificaciones_ids).subscribe({
      next: ({ count }) => {
        this._quitarGrupo(g.id);
        this.sinLeer.update(c => Math.max(0, c - count));
      },
    });
    const url = g.ancla ? `${g.url_accion}${g.ancla}` : g.url_accion;
    if (url) this.router.navigateByUrl(url);
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
    this.accionesId.update(id => id === itemId ? null : itemId);
  }

  onSnooze(event: Event, notifId: string, minutos: number): void {
    event.stopPropagation();
    this.svc.snooze(notifId, minutos).subscribe({
      next: () => {
        this._quitarIndividual(notifId);
        this.sinLeer.update(c => Math.max(0, c - 1));
        this.accionesId.set(null);
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
            this.accionesId.set(null);
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
        this.accionesId.set(null);
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
