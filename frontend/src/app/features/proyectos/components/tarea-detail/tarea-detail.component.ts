/**
 * SaiSuite — TareaDetailComponent
 * Vista detalle de una tarea: metadata, subtareas y seguidores.
 */
import {
  ChangeDetectionStrategy, ChangeDetectorRef,
  Component, OnInit, inject, signal, computed,
} from '@angular/core';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { TareaService } from '../../services/tarea.service';
import { TimesheetService } from '../../services/timesheet.service';
import { ConfiguracionProyectoService } from '../../services/configuracion-proyecto.service';
import { SchedulingService } from '../../services/scheduling.service';
import { TareaCardComponent } from '../tarea-card/tarea-card.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { CronometroComponent } from '../../../../shared/components/cronometro/cronometro.component';
import { ComentariosThreadComponent } from '../../../../shared/components/comentarios-thread/comentarios-thread.component';
import { SelectorDependenciasComponent } from '../selector-dependencias/selector-dependencias.component';
import { ResourceAssignmentPanelComponent } from '../resource-assignment-panel/resource-assignment-panel.component';
import { TaskConstraintsPanelComponent } from '../scheduling/task-constraints-panel/task-constraints-panel.component';
import { FloatIndicatorComponent } from '../scheduling/float-indicator/float-indicator.component';
import { Tarea, TareaEstado, TareaDependencia } from '../../models/tarea.model';
import { TimesheetEntry } from '../../models/timesheet.model';
import type { ModoMedicion } from '../../models/actividad-saiopen.model';
import { ConfiguracionProyecto } from '../../models/configuracion-proyecto.model';
import { SesionTrabajo } from '../../models/sesion-trabajo.model';

export const ESTADO_LABELS: Record<string, string | undefined> = {
  todo:        'Por Hacer',
  in_progress: 'En Progreso',
  in_review:   'En Revisión',
  blocked:     'Bloqueada',
  completed:   'Completada',
  cancelled:   'Cancelada',
};

export const ESTADO_COLORS: Record<string, string | undefined> = {
  todo:        '#9e9e9e',
  in_progress: '#1e88e5',
  in_review:   '#fb8c00',
  blocked:     '#e53935',
  completed:   '#43a047',
  cancelled:   '#757575',
};

export const PRIORIDAD_LABELS: Record<string, string | undefined> = {
  1: 'Baja',
  2: 'Normal',
  3: 'Alta',
  4: 'Urgente',
};

export const PRIORIDAD_ICONS: Record<string, string | undefined> = {
  1: 'arrow_downward',
  2: 'remove',
  3: 'arrow_upward',
  4: 'priority_high',
};

export const PRIORIDAD_COLORS: Record<string, string | undefined> = {
  1: '#43a047',
  2: '#1e88e5',
  3: '#fb8c00',
  4: '#e53935',
};

@Component({
  selector: 'app-tarea-detail',
  templateUrl: './tarea-detail.component.html',
  styleUrl: './tarea-detail.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe, DecimalPipe, FormsModule, RouterLink,
    MatButtonModule, MatIconModule, MatInputModule, MatFormFieldModule,
    MatDatepickerModule, MatNativeDateModule,
    MatProgressBarModule, MatProgressSpinnerModule,
    MatTooltipModule, MatTabsModule, MatDividerModule,
    MatChipsModule,
    TareaCardComponent,
    CronometroComponent,
    ComentariosThreadComponent,
    SelectorDependenciasComponent,
    ResourceAssignmentPanelComponent,
    TaskConstraintsPanelComponent,
    FloatIndicatorComponent,
  ],
})
export class TareaDetailComponent implements OnInit {
  private readonly tareaService       = inject(TareaService);
  private readonly timesheetService   = inject(TimesheetService);
  private readonly configService      = inject(ConfiguracionProyectoService);
  private readonly schedulingService  = inject(SchedulingService);
  private readonly router         = inject(Router);
  private readonly route          = inject(ActivatedRoute);
  private readonly dialog         = inject(MatDialog);
  private readonly snackBar       = inject(MatSnackBar);
  private readonly cdr            = inject(ChangeDetectorRef);

  readonly loading   = signal(true);
  readonly deleting  = signal(false);
  readonly tarea     = signal<Tarea | null>(null);
  readonly returnTo  = signal<'list' | 'kanban'>('list');
  readonly floatDays = signal<number | null>(null);

  // ── Modo de medición (DEC-022) ───────────────────────────────
  readonly modoMedicion = computed<ModoMedicion>(
    () => this.tarea()?.modo_medicion ?? 'solo_estados',
  );

  /** Unidad de medida de la actividad_proyecto asociada ('hora', 'día', etc.) */
  readonly actividadUnidad = computed(() =>
    (this.tarea()?.actividad_proyecto_detail?.actividad_unidad_medida ?? '').toLowerCase().trim(),
  );

  readonly esModoDias = computed(() => {
    const u = this.actividadUnidad();
    return u === 'día' || u === 'dias' || u === 'días' || u === 'dia' || u === 'day' || u === 'days';
  });

  /** Si la actividad usa días, forzar timesheet (backend retorna 'cantidad' para cualquier unidad ≠ 'hora') */
  readonly modoEfectivo = computed<ModoMedicion>(() => {
    if (this.esModoDias()) return 'timesheet';
    return this.modoMedicion();
  });

  readonly unidadLabel       = computed(() => this.esModoDias() ? 'días'        : 'horas');
  readonly unidadLabelCap    = computed(() => this.esModoDias() ? 'Días'        : 'Horas');
  readonly unidadRegistrados = computed(() => this.esModoDias() ? 'registrados' : 'registradas');
  readonly unidadSufijo   = computed(() => this.esModoDias() ? 'd'     : 'h');

  // ── Cantidad inline (modo = 'cantidad') ──────────────────────
  readonly editandoCantidad = signal(false);
  cantidadTemporal = 0;

  onCantidadClick(): void {
    this.cantidadTemporal = 0;
    this.editandoCantidad.set(true);
  }

  onCantidadKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter')  { this.guardarCantidad(); }
    if (event.key === 'Escape') { this.cancelarEdicionCantidad(); }
  }

  guardarCantidad(): void {
    const t = this.tarea();
    if (!t || this.cantidadTemporal <= 0) { this.cancelarEdicionCantidad(); return; }
    this.tareaService.agregarCantidad(t.id, this.cantidadTemporal).subscribe({
      next: (actualizada) => {
        this.tarea.set(actualizada);
        const unidad = t.actividad_proyecto_detail?.actividad_unidad_medida ?? '';
        this.snackBar.open(`${this.cantidadTemporal} ${unidad} agregados.`, 'Cerrar', {
          duration: 2500, panelClass: ['snack-success'],
        });
        this.cancelarEdicionCantidad();
        this.cdr.markForCheck();
      },
      error: (err: { error?: { detail?: string } }) => {
        const msg = err.error?.detail ?? 'Error al agregar cantidad.';
        this.snackBar.open(msg, 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
      },
    });
  }

  cancelarEdicionCantidad(): void {
    this.editandoCantidad.set(false);
    this.cantidadTemporal = 0;
  }

  // ── Timesheet ────────────────────────────────────────────────
  readonly config        = signal<ConfiguracionProyecto | null>(null);
  readonly editandoHoras = signal(false);
  /** Horas adicionales a sumar; propiedad plana para [(ngModel)] */
  horasAdicionales = 0;

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

  // ── Computed ─────────────────────────────────────────────────
  readonly estadoLabel = computed(() => ESTADO_LABELS[this.tarea()?.estado ?? ''] ?? '—');
  readonly estadoColor = computed(() => ESTADO_COLORS[this.tarea()?.estado ?? ''] ?? '#9e9e9e');
  readonly prioridadLabel = computed(() => PRIORIDAD_LABELS[String(this.tarea()?.prioridad ?? '')] ?? '—');
  readonly prioridadIcon  = computed(() => PRIORIDAD_ICONS[String(this.tarea()?.prioridad ?? '')] ?? 'remove');
  readonly prioridadColor = computed(() => PRIORIDAD_COLORS[String(this.tarea()?.prioridad ?? '')] ?? '#9e9e9e');

  // Constantes para el template
  readonly estadoLabels   = ESTADO_LABELS;
  readonly estadoColors   = ESTADO_COLORS;
  readonly prioridadLabels = PRIORIDAD_LABELS;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      this.router.navigate(['/proyectos/tareas']);
      return;
    }
    const ret = this.route.snapshot.queryParamMap.get('returnTo');
    if (ret === 'kanban') this.returnTo.set('kanban');
    this.loadTarea(id);
    this.loadConfig();
  }

  private loadConfig(): void {
    this.configService.obtener().subscribe({
      next: (c) => { this.config.set(c); this.cdr.markForCheck(); },
      error: () => { /* sin config: timesheet desactivado por defecto */ },
    });
  }

  private loadTarea(id: string): void {
    this.loading.set(true);
    this.tareaService.getById(id).subscribe({
      next: (tarea) => {
        this.tarea.set(tarea);
        this.loading.set(false);
        this.cargarEntries(tarea.id);
        // Cargar float real solo si la tarea no es crítica (crítica → float=0)
        if (!tarea.es_camino_critico) {
          this.schedulingService.getTaskFloat(tarea.id).subscribe({
            next: (fd) => { this.floatDays.set(fd.total_float); this.cdr.markForCheck(); },
            error: () => { /* sin datos CPM: floatDays queda null */ },
          });
        }
        this.cdr.markForCheck();
      },
      error: () => {
        this.snackBar.open('No se pudo cargar la tarea.', 'Cerrar', {
          duration: 4000, panelClass: ['snack-error'],
        });
        this.loading.set(false);
        this.router.navigate(['/proyectos/tareas']);
      },
    });
  }

  editar(): void {
    const t = this.tarea();
    if (t) this.router.navigate(['/proyectos/tareas', t.id, 'editar']);
  }

  nuevaSubtarea(): void {
    const t = this.tarea();
    if (t) {
      this.router.navigate(['/proyectos/tareas/nueva'], {
        queryParams: { proyecto: t.proyecto, padre: t.id },
      });
    }
  }

  editarSubtarea(subtarea: Tarea): void {
    this.router.navigate(['/proyectos/tareas', subtarea.id, 'editar']);
  }

  verSubtarea(subtarea: Tarea): void {
    this.router.navigate(['/proyectos/tareas', subtarea.id]);
  }

  confirmarEliminar(): void {
    const t = this.tarea();
    if (!t) return;
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header:      'Eliminar tarea',
        message:     `¿Eliminar la tarea "${t.nombre}"? Esta acción no se puede deshacer.`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
      width: '420px',
    });
    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) this.eliminar();
    });
  }

  private eliminar(): void {
    const t = this.tarea();
    if (!t) return;
    this.deleting.set(true);
    this.tareaService.delete(t.id).subscribe({
      next: () => {
        this.snackBar.open('Tarea eliminada correctamente.', 'Cerrar', {
          duration: 3000, panelClass: ['snack-success'],
        });
        this.router.navigate(['/proyectos/tareas']);
      },
      error: () => {
        this.snackBar.open('No se pudo eliminar la tarea.', 'Cerrar', {
          duration: 4000, panelClass: ['snack-error'],
        });
        this.deleting.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  cambiarEstado(nuevoEstado: TareaEstado): void {
    const t = this.tarea();
    if (!t) return;
    this.tareaService.cambiarEstado(t.id, nuevoEstado).subscribe({
      next: (updated) => {
        this.tarea.set(updated);
        this.snackBar.open(
          `Estado cambiado a "${ESTADO_LABELS[nuevoEstado] ?? nuevoEstado}".`,
          'Cerrar', { duration: 2500, panelClass: ['snack-success'] },
        );
        this.cdr.markForCheck();
      },
      error: (err: { error?: { detail?: string } }) => {
        const msg = err.error?.detail ?? 'No se pudo cambiar el estado.';
        this.snackBar.open(msg, 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
      },
    });
  }

  volver(): void {
    this.router.navigate([
      this.returnTo() === 'kanban' ? '/proyectos/tareas/kanban' : '/proyectos/tareas',
    ]);
  }

  verTareaPadre(): void {
    const t = this.tarea();
    if (t?.tarea_padre) this.router.navigate(['/proyectos/tareas', t.tarea_padre]);
  }

  /** Estados disponibles para el selector de cambio rápido */
  readonly estadosDisponibles: TareaEstado[] = [
    'todo', 'in_progress', 'in_review', 'blocked', 'completed', 'cancelled',
  ];

  // ── Dependencias ──────────────────────────────────────────────

  onDependenciaAgregada(dep: TareaDependencia): void {
    const t = this.tarea();
    if (!t) return;
    this.tarea.set({
      ...t,
      predecesoras_detail: [...(t.predecesoras_detail ?? []), dep],
    });
    this.cdr.markForCheck();
  }

  onDependenciaEliminada(depId: string): void {
    const t = this.tarea();
    if (!t) return;
    this.tarea.set({
      ...t,
      predecesoras_detail: (t.predecesoras_detail ?? []).filter(d => d.id !== depId),
    });
    this.cdr.markForCheck();
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
        this.snackBar.open(
          `${horas} ${this.unidadLabel()} agregados correctamente.`,
          'Cerrar',
          { duration: 2500, panelClass: ['snack-success'] },
        );
        this.cancelarEdicionHoras();
        this.cdr.markForCheck();
      },
      error: (err: { error?: { detail?: string } }) => {
        const msg = err.error?.detail ?? 'Error al agregar horas.';
        this.snackBar.open(msg, 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
      },
    });
  }

  cancelarEdicionHoras(): void {
    this.editandoHoras.set(false);
    this.horasAdicionales = 0;
  }

  // ── Timesheet: cronómetro ─────────────────────────────────────

  onSesionFinalizada(_sesion: SesionTrabajo): void {
    const t = this.tarea();
    if (t) {
      this.loadTarea(t.id);
      this.cargarEntries(t.id);
    }
  }

  // ── Timesheet: registros diarios (TimesheetEntry) ─────────────

  readonly timesheetEntries   = signal<TimesheetEntry[]>([]);
  readonly loadingEntries     = signal(false);
  readonly guardandoEntry     = signal(false);
  readonly mostrarFormEntry   = signal(false);

  // Campos del formulario manual
  entryFecha:      Date | null = new Date();
  entryHoras       = 1;
  entryDescripcion = '';

  cargarEntries(tareaId: string): void {
    this.loadingEntries.set(true);
    this.timesheetService.list({ tarea: tareaId }).subscribe({
      next: (entries) => {
        this.timesheetEntries.set(entries);
        this.loadingEntries.set(false);
        this.cdr.markForCheck();
      },
      error: () => this.loadingEntries.set(false),
    });
  }

  registrarEntryManual(): void {
    const t = this.tarea();
    if (!t) return;
    if (!this.entryFecha || this.entryHoras <= 0) {
      this.snackBar.open('Fecha y días son obligatorios.', 'Cerrar', {
        duration: 3000, panelClass: ['snack-error'],
      });
      return;
    }
    this.guardandoEntry.set(true);
    this.timesheetService.create({
      tarea_id:    t.id,
      fecha:       this.isoFromDate(this.entryFecha),
      horas:       this.entryHoras,
      descripcion: this.entryDescripcion,
    }).subscribe({
      next: () => {
        this.mostrarFormEntry.set(false);
        this.entryFecha       = new Date();
        this.entryHoras       = 1;
        this.entryDescripcion = '';
        this.snackBar.open(`${this.unidadLabelCap()} ${this.unidadRegistrados()}.`, 'Cerrar', {
          duration: 3000, panelClass: ['snack-success'],
        });
        this.loadTarea(t.id);
        this.cargarEntries(t.id);
        this.guardandoEntry.set(false);
        this.cdr.markForCheck();
      },
      error: (err: { error?: { detail?: string } }) => {
        const msg = err.error?.detail ?? 'No se pudo registrar las horas.';
        this.snackBar.open(msg, 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
        this.guardandoEntry.set(false);
      },
    });
  }

  eliminarEntry(entry: TimesheetEntry): void {
    const t = this.tarea();
    if (!t) return;
    this.timesheetService.delete(entry.id).subscribe({
      next: () => {
        this.snackBar.open('Registro eliminado.', 'Cerrar', {
          duration: 2500, panelClass: ['snack-success'],
        });
        this.loadTarea(t.id);
      },
      error: (err: { error?: { detail?: string } }) => {
        const msg = err.error?.detail ?? 'No se pudo eliminar.';
        this.snackBar.open(msg, 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
      },
    });
  }

  hoy(): Date {
    return new Date();
  }

  private isoFromDate(d: Date | null): string {
    if (!d) return new Date().toISOString().slice(0, 10);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
}
