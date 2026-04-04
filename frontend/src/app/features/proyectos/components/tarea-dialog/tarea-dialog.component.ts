/**
 * SaiSuite — TareaDialogComponent
 * Modal de vista rápida de tarea abierto desde el Kanban.
 * Permite cambiar estado sin salir del tablero.
 */
import {
  ChangeDetectionStrategy, ChangeDetectorRef,
  Component, OnInit, inject, signal, computed,
} from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import {
  MatDialogRef,
  MAT_DIALOG_DATA,
  MatDialogModule,
} from '@angular/material/dialog';
import { TareaService } from '../../services/tarea.service';
import { ConfiguracionProyectoService } from '../../services/configuracion-proyecto.service';
import { TareaCardComponent } from '../tarea-card/tarea-card.component';
import { CronometroComponent } from '../../../../shared/components/cronometro/cronometro.component';
import { ComentariosThreadComponent } from '../../../../shared/components/comentarios-thread/comentarios-thread.component';
import { Tarea, TareaEstado } from '../../models/tarea.model';
import { ConfiguracionProyecto } from '../../models/configuracion-proyecto.model';
import { SesionTrabajo } from '../../models/sesion-trabajo.model';
import { ToastService } from '../../../../core/services/toast.service';

export interface TareaDialogData {
  tareaId: string;
}

export interface TareaDialogResult {
  updated: boolean;
  tarea?: Tarea;
  /** Si se establece, el Kanban navega a esta ruta al cerrar en vez de limpiar la URL. */
  navigateTo?: string[];
  navigateParams?: Record<string, string>;
}

const ESTADO_LABELS: Record<string, string | undefined> = {
  todo:        'Por Hacer',
  in_progress: 'En Progreso',
  in_review:   'En Revisión',
  blocked:     'Bloqueada',
  completed:   'Completada',
  cancelled:   'Cancelada',
};

const ESTADO_COLORS: Record<string, string | undefined> = {
  todo:        '#9e9e9e',
  in_progress: '#1e88e5',
  in_review:   '#fb8c00',
  blocked:     '#e53935',
  completed:   '#43a047',
  cancelled:   '#757575',
};

const PRIORIDAD_LABELS: Record<string, string | undefined> = {
  1: 'Baja',
  2: 'Normal',
  3: 'Alta',
  4: 'Urgente',
};

const PRIORIDAD_COLORS: Record<string, string | undefined> = {
  1: '#43a047',
  2: '#1e88e5',
  3: '#fb8c00',
  4: '#e53935',
};

const PRIORIDAD_ICONS: Record<string, string | undefined> = {
  1: 'arrow_downward',
  2: 'remove',
  3: 'arrow_upward',
  4: 'priority_high',
};

@Component({
  selector: 'app-tarea-dialog',
  templateUrl: './tarea-dialog.component.html',
  styleUrl: './tarea-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe, DecimalPipe, FormsModule,
    MatButtonModule, MatIconModule,
    MatProgressBarModule, MatProgressSpinnerModule,
    MatTabsModule, MatDividerModule, MatTooltipModule,
    MatDialogModule,
    TareaCardComponent, CronometroComponent, ComentariosThreadComponent,
  ],
})
export class TareaDialogComponent implements OnInit {
  private readonly dialogRef     = inject<MatDialogRef<TareaDialogComponent, TareaDialogResult>>(MatDialogRef);
  private readonly data          = inject<TareaDialogData>(MAT_DIALOG_DATA);
  private readonly tareaService  = inject(TareaService);
  private readonly configService = inject(ConfiguracionProyectoService);
  private readonly toast       = inject(ToastService);
  private readonly cdr           = inject(ChangeDetectorRef);

  readonly loading  = signal(true);
  readonly changing = signal(false);
  readonly tarea    = signal<Tarea | null>(null);

  // ── Timesheet ────────────────────────────────────────────────
  readonly config           = signal<ConfiguracionProyecto | null>(null);
  readonly editandoHoras    = signal(false);
  readonly editandoCantidad = signal(false);
  /** Propiedades planas para [(ngModel)] — signals no son compatibles con ngModel */
  horasAdicionales    = 0;
  cantidadAdicional   = 0;

  readonly modoManualHabilitado = computed(() => {
    const m = this.config()?.modo_timesheet;
    return m === 'manual' || m === 'ambos';
  });
  readonly modoCronometroHabilitado = computed(() => {
    const m = this.config()?.modo_timesheet;
    return m === 'cronometro' || m === 'ambos';
  });
  readonly modoTimesheetDesactivado = computed(() =>
    this.config() !== null && this.config()!.modo_timesheet === 'desactivado'
  );

  readonly estadoLabel   = computed(() => ESTADO_LABELS[this.tarea()?.estado ?? ''] ?? '—');
  readonly estadoColor   = computed(() => ESTADO_COLORS[this.tarea()?.estado ?? ''] ?? '#9e9e9e');
  readonly prioridadLabel = computed(() => PRIORIDAD_LABELS[String(this.tarea()?.prioridad ?? '')] ?? '—');
  readonly prioridadColor = computed(() => PRIORIDAD_COLORS[String(this.tarea()?.prioridad ?? '')] ?? '#9e9e9e');
  readonly prioridadIcon  = computed(() => PRIORIDAD_ICONS[String(this.tarea()?.prioridad ?? '')] ?? 'remove');

  readonly modoMedicion  = computed(() => this.tarea()?.modo_medicion ?? 'solo_estados');
  readonly unidadMedida  = computed(() =>
    this.tarea()?.actividad_proyecto_detail?.actividad_unidad_medida ?? ''
  );
  readonly progreso = computed(() => {
    const t = this.tarea();
    if (!t) return 0;
    if (this.modoMedicion() === 'timesheet' && t.horas_estimadas > 0) return t.progreso_porcentaje;
    if (this.modoMedicion() === 'cantidad' && t.cantidad_objetivo > 0) return t.progreso_porcentaje;
    return t.porcentaje_completado;
  });

  readonly estadoLabels  = ESTADO_LABELS;
  readonly estadoColors  = ESTADO_COLORS;

  readonly estadosDisponibles: TareaEstado[] = [
    'todo', 'in_progress', 'in_review', 'blocked', 'completed', 'cancelled',
  ];

  ngOnInit(): void {
    this.tareaService.getById(this.data.tareaId).subscribe({
      next: (tarea) => {
        this.tarea.set(tarea);
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.toast.error('No se pudo cargar la tarea.');
        this.dialogRef.close();
      },
    });
    this.configService.obtener().subscribe({
      next: (c) => { this.config.set(c); this.cdr.markForCheck(); },
      error: () => { /* sin config: timesheet desactivado por defecto */ },
    });
  }

  cambiarEstado(nuevoEstado: TareaEstado): void {
    const t = this.tarea();
    if (!t || this.changing()) return;
    this.changing.set(true);
    this.tareaService.cambiarEstado(t.id, nuevoEstado).subscribe({
      next: (updated) => {
        this.tarea.set(updated);
        this.changing.set(false);
        this.toast.success(`Estado cambiado a "${ESTADO_LABELS[nuevoEstado] ?? nuevoEstado}".`);
        this.cdr.markForCheck();
        // Notificar al Kanban que hubo cambio
        this.dialogRef.close({ updated: true, tarea: updated });
      },
      error: (err: { error?: { detail?: string } }) => {
        const msg = err.error?.detail ?? 'No se pudo cambiar el estado.';
        this.toast.error(msg);
        this.changing.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  verDetalleCompleto(): void {
    const t = this.tarea();
    if (!t) return;
    this.dialogRef.close({
      updated: false,
      navigateTo: ['/proyectos/tareas', t.id],
    });
  }

  editarTarea(): void {
    const t = this.tarea();
    if (!t) return;
    this.dialogRef.close({
      updated: false,
      navigateTo: ['/proyectos/tareas', t.id, 'editar'],
    });
  }

  cerrar(): void {
    this.dialogRef.close();
  }

  verSubtarea(subtarea: Tarea): void {
    this.dialogRef.close({
      updated: false,
      navigateTo: ['/proyectos/tareas', subtarea.id],
    });
  }

  // ── Timesheet: modo manual ────────────────────────────────────

  onHorasClick(): void {
    this.horasAdicionales = 0;
    this.editandoHoras.set(true);
  }

  onHorasKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter')  { this.guardarHoras(); }
    if (event.key === 'Escape') { this.cancelarEdicionHoras(); }
  }

  guardarHoras(): void {
    const horas = this.horasAdicionales;
    const tarea = this.tarea();
    if (!tarea || horas <= 0) { this.cancelarEdicionHoras(); return; }

    this.tareaService.agregarHoras(tarea.id, horas).subscribe({
      next: (actualizada) => {
        this.tarea.set(actualizada);
        this.toast.success(`${horas}h agregadas correctamente.`);
        this.cancelarEdicionHoras();
        this.cdr.markForCheck();
      },
      error: (err: { error?: { detail?: string } }) => {
        const msg = err.error?.detail ?? 'Error al agregar horas.';
        this.toast.error(msg);
      },
    });
  }

  cancelarEdicionHoras(): void {
    this.editandoHoras.set(false);
    this.horasAdicionales = 0;
  }

  // ── Cantidad: modo manual ─────────────────────────────────

  onCantidadClick(): void {
    this.cantidadAdicional = 0;
    this.editandoCantidad.set(true);
  }

  onCantidadKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter')  { this.guardarCantidad(); }
    if (event.key === 'Escape') { this.cancelarEdicionCantidad(); }
  }

  guardarCantidad(): void {
    const cantidad = this.cantidadAdicional;
    const tarea = this.tarea();
    if (!tarea || cantidad <= 0) { this.cancelarEdicionCantidad(); return; }

    this.tareaService.agregarCantidad(tarea.id, cantidad).subscribe({
      next: (actualizada) => {
        this.tarea.set(actualizada);
        const unidad = this.unidadMedida();
        this.toast.success(`${cantidad} ${unidad} agregados correctamente.`);
        this.cancelarEdicionCantidad();
        this.cdr.markForCheck();
      },
      error: (err: { error?: { detail?: string } }) => {
        const msg = err.error?.detail ?? 'Error al agregar cantidad.';
        this.toast.error(msg);
      },
    });
  }

  cancelarEdicionCantidad(): void {
    this.editandoCantidad.set(false);
    this.cantidadAdicional = 0;
  }

  // ── Timesheet: cronómetro ─────────────────────────────────────

  onSesionFinalizada(_sesion: SesionTrabajo): void {
    const t = this.tarea();
    if (!t) return;
    // Recargar tarea para actualizar horas_registradas
    this.tareaService.getById(t.id).subscribe({
      next: (actualizada) => { this.tarea.set(actualizada); this.cdr.markForCheck(); },
      error: () => { /* silencioso */ },
    });
  }
}
