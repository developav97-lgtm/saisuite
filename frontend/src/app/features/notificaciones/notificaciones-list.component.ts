/**
 * SaiSuite — NotificacionesListComponent
 * Página completa de notificaciones con filtros, paginación y acciones CRUD.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { FormsModule } from '@angular/forms';
import { NotificacionesService } from '../../core/services/notificaciones.service';
import { Notificacion, TipoNotificacion } from '../../shared/models/notificacion.model';
import { ToastService } from '../../core/services/toast.service';

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
};

const TIPO_LABELS: Record<string, string> = {
  comentario:           'Comentario',
  mencion:              'Mención',
  aprobacion:           'Aprobación',
  aprobacion_resultado: 'Resultado aprobación',
  asignacion:           'Asignación',
  cambio_estado:        'Cambio de estado',
  vencimiento:          'Vencimiento',
  sistema:              'Sistema',
  chat:                 'Chat',
};

interface TipoOption { label: string; value: TipoNotificacion | null; }

@Component({
  selector: 'app-notificaciones-list',
  templateUrl: './notificaciones-list.component.html',
  styleUrl: './notificaciones-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, FormsModule,
    MatButtonModule, MatIconModule,
    MatFormFieldModule, MatSelectModule,
    MatPaginatorModule, MatProgressSpinnerModule,
    MatTooltipModule, MatDividerModule,
  ],
})
export class NotificacionesListComponent implements OnInit {
  private readonly svc      = inject(NotificacionesService);
  private readonly router   = inject(Router);
  private readonly toast       = inject(ToastService);

  readonly notificaciones = signal<Notificacion[]>([]);
  readonly totalCount     = signal(0);
  readonly loading        = signal(false);
  readonly marcando       = signal(false);

  /** Propiedades planas para ngModel (signals no son compatibles con ngModel) */
  leidaFilter: boolean | null = null;
  tipoFilter:  TipoNotificacion | null = null;

  readonly pageSize    = 20;
  readonly currentPage = signal(0);

  readonly TIPO_ICONS  = TIPO_ICONS;
  readonly TIPO_LABELS = TIPO_LABELS;

  readonly leidaOptions = [
    { label: 'Todas',        value: null  },
    { label: 'No leídas',    value: false },
    { label: 'Leídas',       value: true  },
  ];

  readonly tipoOptions: TipoOption[] = [
    { label: 'Todos los tipos', value: null },
    ...Object.entries(TIPO_LABELS).map(([value, label]) => ({
      label,
      value: value as TipoNotificacion,
    })),
  ];

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    const filters: Parameters<typeof this.svc.listar>[0] = {
      page:      this.currentPage() + 1,
      page_size: this.pageSize,
    };
    if (this.leidaFilter !== null) filters.leida = this.leidaFilter;
    if (this.tipoFilter)           filters.tipo  = this.tipoFilter;

    this.svc.listar(filters).subscribe({
      next: (r) => {
        this.notificaciones.set(r.results);
        this.totalCount.set(r.count);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('No se pudieron cargar las notificaciones.');
        this.loading.set(false);
      },
    });
  }

  onFilterChange(): void {
    this.currentPage.set(0);
    this.cargar();
  }

  onPage(event: PageEvent): void {
    this.currentPage.set(event.pageIndex);
    this.cargar();
  }

  onNotificacionClick(n: Notificacion): void {
    if (!n.leida) {
      this.svc.marcarLeida(n.id).subscribe({
        next: () => {
          this.notificaciones.update(list =>
            list.map(x => x.id === n.id ? { ...x, leida: true } : x)
          );
        },
      });
    }
    const url = n.ancla ? `${n.url_accion}${n.ancla}` : n.url_accion;
    if (url) this.router.navigateByUrl(url);
  }

  marcarLeida(event: Event, n: Notificacion): void {
    event.stopPropagation();
    if (n.leida) return;
    this.svc.marcarLeida(n.id).subscribe({
      next: () => {
        this.notificaciones.update(list =>
          list.map(x => x.id === n.id ? { ...x, leida: true } : x)
        );
      },
    });
  }

  marcarNoLeida(event: Event, n: Notificacion): void {
    event.stopPropagation();
    if (!n.leida) return;
    this.svc.marcarNoLeida(n.id).subscribe({
      next: () => {
        this.notificaciones.update(list =>
          list.map(x => x.id === n.id ? { ...x, leida: false } : x)
        );
      },
    });
  }

  marcarTodasLeidas(): void {
    this.marcando.set(true);
    this.svc.marcarTodasLeidas().subscribe({
      next: () => {
        this.marcando.set(false);
        this.toast.success('Todas las notificaciones marcadas como leídas.');
        this.cargar();
      },
      error: () => {
        this.marcando.set(false);
        this.toast.error('No se pudieron marcar las notificaciones.');
      },
    });
  }

  getTipoIcon(tipo: string): string {
    return TIPO_ICONS[tipo] ?? 'notifications';
  }

  formatTiempo(fecha: string): string {
    const diff   = Date.now() - new Date(fecha).getTime();
    const min    = Math.floor(diff / 60_000);
    const horas  = Math.floor(diff / 3_600_000);
    const dias   = Math.floor(diff / 86_400_000);
    if (min < 1)    return 'Ahora';
    if (min < 60)   return `Hace ${min}m`;
    if (horas < 24) return `Hace ${horas}h`;
    if (dias < 7)   return `Hace ${dias}d`;
    return new Date(fecha).toLocaleDateString('es-CO');
  }
}
