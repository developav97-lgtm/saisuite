import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  inject,
  input,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBar } from '@angular/material/snack-bar';
import { FormsModule } from '@angular/forms';
import Gantt, { type FrappeGanttTask, type ViewMode } from 'frappe-gantt';
import { ProyectoService } from '../../services/proyecto.service';
import { TareaService } from '../../services/tarea.service';
import { SchedulingService } from '../../services/scheduling.service';
import { BaselineService } from '../../services/baseline.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import type { ProjectBaselineList } from '../../models/baseline.model';

@Component({
  selector: 'app-gantt-view',
  templateUrl: './gantt-view.component.html',
  styleUrl: './gantt-view.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatButtonToggleModule,
    MatButtonModule,
    MatDialogModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatChipsModule,
  ],
})
export class GanttViewComponent implements AfterViewInit, OnDestroy {
  @ViewChild('ganttContainer') ganttContainer!: ElementRef<SVGElement>;

  readonly proyectoId = input.required<string>();

  private readonly proyectoService  = inject(ProyectoService);
  private readonly tareaService     = inject(TareaService);
  private readonly schedulingService = inject(SchedulingService);
  private readonly baselineService  = inject(BaselineService);
  private readonly router           = inject(Router);
  private readonly dialog           = inject(MatDialog);
  private readonly snackBar         = inject(MatSnackBar);
  private readonly cdr              = inject(ChangeDetectorRef);

  readonly loading  = signal(true);
  readonly hasData  = signal(false);
  viewMode: ViewMode = 'Week';

  // ── SK-41: Scheduling overlays ────────────────────────────────────────────
  readonly showCriticalPath  = signal(false);
  readonly showFloat         = signal(false);
  readonly showBaseline      = signal(false);
  readonly loadingOverlay    = signal(false);

  private criticalTaskIds    = new Set<string>();
  private floatMap           = new Map<string, number | null>();
  readonly activeBaseline    = signal<ProjectBaselineList | null>(null);

  private ganttInstance: Gantt | null = null;
  private tasks: FrappeGanttTask[]    = [];

  /** Flag para distinguir drag de click simple */
  private wasDragged = false;
  /** Timeout del debounce de on_date_change */
  private dateChangeTimer?: ReturnType<typeof setTimeout>;

  readonly LEGEND = [
    { clase: 'estado-todo',        label: 'Por hacer'   },
    { clase: 'estado-in_progress', label: 'En progreso' },
    { clase: 'estado-in_review',   label: 'En revisión' },
    { clase: 'estado-blocked',     label: 'Bloqueada'   },
    { clase: 'estado-completed',   label: 'Completada'  },
    { clase: 'estado-cancelled',   label: 'Cancelada'   },
  ];

  ngAfterViewInit(): void {
    this.cargarGantt();
  }

  ngOnDestroy(): void {
    this.ganttInstance = null;
    clearTimeout(this.dateChangeTimer);
  }

  cargarGantt(): void {
    this.loading.set(true);
    this.proyectoService.getGanttData(this.proyectoId()).subscribe({
      next: ({ tasks }) => {
        this.loading.set(false);
        if (!tasks.length) {
          this.hasData.set(false);
          this.cdr.detectChanges();
          return;
        }
        this.tasks = tasks.map(t => ({
          id:           t.id,
          name:         t.name,
          start:        t.start,
          end:          t.end,
          progress:     t.progress,
          custom_class: t.custom_class,
        }));
        this.hasData.set(true);
        this.cdr.detectChanges();
        this.initGantt();
      },
      error: () => {
        this.loading.set(false);
        this.hasData.set(false);
        this.cdr.detectChanges();
      },
    });
  }

  // ── SK-41: Toggle ruta crítica ────────────────────────────────────────────

  toggleCriticalPath(): void {
    const next = !this.showCriticalPath();
    this.showCriticalPath.set(next);
    if (next && this.criticalTaskIds.size === 0) {
      this.loadCriticalPath();
    } else {
      this.rerenderGantt();
    }
  }

  private loadCriticalPath(): void {
    this.loadingOverlay.set(true);
    this.schedulingService.getCriticalPath(this.proyectoId()).subscribe({
      next: (data) => {
        this.criticalTaskIds = new Set(data.critical_path);
        this.loadingOverlay.set(false);
        this.rerenderGantt();
      },
      error: () => {
        this.loadingOverlay.set(false);
        this.showCriticalPath.set(false);
        this.snackBar.open('No se pudo calcular la ruta crítica.', 'Cerrar', {
          duration: 4000, panelClass: ['snack-error'],
        });
      },
    });
  }

  // ── SK-41: Toggle float ───────────────────────────────────────────────────

  toggleFloat(): void {
    const next = !this.showFloat();
    this.showFloat.set(next);
    if (next && this.floatMap.size === 0) {
      this.loadFloatData();
    } else {
      this.rerenderGantt();
    }
  }

  private loadFloatData(): void {
    this.loadingOverlay.set(true);
    this.schedulingService.getCriticalPath(this.proyectoId()).subscribe({
      next: (data) => {
        // Usamos el CPM para poblar el float de cada tarea crítica (float=0)
        // Para tareas no críticas no tenemos float por tarea sin llamadas individuales;
        // marcamos las críticas con float=0, resto como null (sin dato)
        this.floatMap.clear();
        data.critical_path.forEach(id => this.floatMap.set(id, 0));
        this.loadingOverlay.set(false);
        this.rerenderGantt();
      },
      error: () => {
        this.loadingOverlay.set(false);
        this.showFloat.set(false);
      },
    });
  }

  // ── SK-41: Toggle baseline ────────────────────────────────────────────────

  toggleBaseline(): void {
    const next = !this.showBaseline();
    this.showBaseline.set(next);
    if (next && !this.activeBaseline()) {
      this.loadActiveBaseline();
    }
  }

  private loadActiveBaseline(): void {
    this.loadingOverlay.set(true);
    this.baselineService.list(this.proyectoId()).subscribe({
      next: (list) => {
        const active = list.find(b => b.is_active_baseline) ?? list[0] ?? null;
        this.activeBaseline.set(active);
        this.loadingOverlay.set(false);
        this.cdr.detectChanges();
      },
      error: () => {
        this.loadingOverlay.set(false);
        this.showBaseline.set(false);
      },
    });
  }

  // ── Renderizado con overlays ──────────────────────────────────────────────

  private rerenderGantt(): void {
    const renderTasks = this.tasks.map(t => {
      let customClass = t.custom_class ?? '';
      let name        = t.name;

      if (this.showCriticalPath() && this.criticalTaskIds.has(t.id)) {
        customClass = `${customClass} critical-task`.trim();
      }
      if (this.showFloat()) {
        const f = this.floatMap.get(t.id);
        if (f === 0) {
          name = `${name} [CRÍTICA]`;
        } else if (f !== undefined && f !== null && f > 0) {
          name = `${name} [Float: ${f}d]`;
        }
      }
      return { ...t, custom_class: customClass, name };
    });

    this.tasks = this.tasks; // mantener base sin modificar
    const el = this.ganttContainer?.nativeElement;
    if (!el) return;
    el.innerHTML = '';
    const rowHeight = Math.max(52, Math.floor((window.innerHeight - 320) / (renderTasks.length + 1)));
    this.ganttInstance = new Gantt(el, renderTasks, {
      view_mode:  this.viewMode,
      language:   'es',
      bar_height: rowHeight - 16,
      padding:    16,
      on_date_change: (task: FrappeGanttTask, start: Date, end: Date) => {
        clearTimeout(this.dateChangeTimer);
        this.dateChangeTimer = setTimeout(() => {
          this.wasDragged = true;
          this.confirmarCambioFechas(task, start, end);
        }, 400);
      },
      on_click: (task: FrappeGanttTask) => {
        if (this.wasDragged) { this.wasDragged = false; return; }
        void this.router.navigate(['/proyectos', this.proyectoId(), 'tareas', task.id]);
      },
    });
  }

  private initGantt(): void {
    this.rerenderGantt();
  }

  private confirmarCambioFechas(task: FrappeGanttTask, start: Date, end: Date): void {
    const fmt = (d: Date) =>
      d.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' });

    const ref = this.dialog.open(ConfirmDialogComponent, {
      width: '420px',
      data: {
        header:      'Confirmar cambio de fechas',
        message:     `¿Actualizar las fechas de "${task.name}"?\n\nNuevo rango: ${fmt(start)} → ${fmt(end)}`,
        acceptLabel: 'Actualizar',
        acceptColor: 'primary',
      },
    });

    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) {
        // Revertir el Gantt al estado anterior
        this.cargarGantt();
        return;
      }

      const toISO = (d: Date) => d.toISOString().split('T')[0];

      this.tareaService.update(task.id, {
        fecha_inicio: toISO(start),
        fecha_fin:    toISO(end),
      }).subscribe({
        next: () => {
          this.snackBar.open('Fechas actualizadas correctamente.', 'Cerrar', {
            duration: 3000, panelClass: ['snack-success'],
          });
        },
        error: () => {
          this.snackBar.open('No se pudieron actualizar las fechas.', 'Cerrar', {
            duration: 4000, panelClass: ['snack-error'],
          });
          this.cargarGantt();
        },
      });
    });
  }

  onViewModeChange(): void {
    if (this.ganttInstance) {
      this.ganttInstance.change_view_mode(this.viewMode);
    }
  }

  refreshGantt(): void {
    this.cargarGantt();
  }
}
