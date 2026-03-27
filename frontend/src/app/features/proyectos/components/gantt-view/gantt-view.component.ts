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
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar } from '@angular/material/snack-bar';
import { FormsModule } from '@angular/forms';
import Gantt, { type FrappeGanttTask, type ViewMode } from 'frappe-gantt';
import { ProyectoService } from '../../services/proyecto.service';
import { TareaService } from '../../services/tarea.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-gantt-view',
  templateUrl: './gantt-view.component.html',
  styleUrl: './gantt-view.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatButtonToggleModule,
    MatDialogModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
})
export class GanttViewComponent implements AfterViewInit, OnDestroy {
  @ViewChild('ganttContainer') ganttContainer!: ElementRef<SVGElement>;

  readonly proyectoId = input.required<string>();

  private readonly proyectoService = inject(ProyectoService);
  private readonly tareaService    = inject(TareaService);
  private readonly router          = inject(Router);
  private readonly dialog          = inject(MatDialog);
  private readonly snackBar        = inject(MatSnackBar);
  private readonly cdr             = inject(ChangeDetectorRef);

  readonly loading  = signal(true);
  readonly hasData  = signal(false);
  viewMode: ViewMode = 'Week';

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
      },
    });
  }

  private initGantt(): void {
    const el = this.ganttContainer?.nativeElement;
    if (!el) return;

    el.innerHTML = '';

    const rowHeight = Math.max(52, Math.floor((window.innerHeight - 320) / (this.tasks.length + 1)));

    this.ganttInstance = new Gantt(el, this.tasks, {
      view_mode:  this.viewMode,
      language:   'es',
      bar_height: rowHeight - 16,
      padding:    16,

      on_date_change: (task: FrappeGanttTask, start: Date, end: Date) => {
        // Frappe Gantt llama on_date_change durante cada movimiento del drag.
        // Debounce: solo actuar 400ms después del último evento (= cuando soltó).
        clearTimeout(this.dateChangeTimer);
        this.dateChangeTimer = setTimeout(() => {
          this.wasDragged = true;
          this.confirmarCambioFechas(task, start, end);
        }, 400);
      },

      on_click: (task: FrappeGanttTask) => {
        // Ignorar si el evento viene de soltar un drag
        if (this.wasDragged) {
          this.wasDragged = false;
          return;
        }
        void this.router.navigate(['/proyectos', this.proyectoId(), 'tareas', task.id]);
      },
    });
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
