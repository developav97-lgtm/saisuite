import {
  AfterViewInit,
  ChangeDetectionStrategy,
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
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormsModule } from '@angular/forms';
import Gantt, { type FrappeGanttTask, type ViewMode } from 'frappe-gantt';
import { ProyectoService } from '../../services/proyecto.service';

@Component({
  selector: 'app-gantt-view',
  templateUrl: './gantt-view.component.html',
  styleUrl: './gantt-view.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatButtonToggleModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
})
export class GanttViewComponent implements AfterViewInit, OnDestroy {
  @ViewChild('ganttContainer') ganttContainer!: ElementRef<SVGElement>;

  readonly proyectoId = input.required<string>();

  private readonly proyectoService = inject(ProyectoService);
  private readonly router          = inject(Router);

  readonly loading  = signal(true);
  readonly hasData  = signal(false);
  viewMode: ViewMode = 'Week';

  private ganttInstance: Gantt | null = null;
  private tasks: FrappeGanttTask[]    = [];

  readonly LEGEND = [
    { clase: 'estado-por_hacer',   label: 'Por hacer'   },
    { clase: 'estado-en_progreso', label: 'En progreso' },
    { clase: 'estado-en_revision', label: 'En revisión' },
    { clase: 'estado-bloqueada',   label: 'Bloqueada'   },
    { clase: 'estado-completada',  label: 'Completada'  },
    { clase: 'estado-cancelada',   label: 'Cancelada'   },
  ];

  ngAfterViewInit(): void {
    this.cargarGantt();
  }

  ngOnDestroy(): void {
    this.ganttInstance = null;
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
        // Give Angular one microtask to render the SVG element before initializing
        Promise.resolve().then(() => this.initGantt());
      },
      error: () => {
        this.loading.set(false);
        this.hasData.set(false);
      },
    });
  }

  private initGantt(): void {
    if (!this.ganttContainer?.nativeElement) return;

    this.ganttInstance = new Gantt(
      this.ganttContainer.nativeElement,
      this.tasks,
      {
        view_mode:  this.viewMode,
        language:   'es',
        bar_height: 28,
        padding:    16,
        on_click: (task: FrappeGanttTask) => {
          void this.router.navigate(['/proyectos', this.proyectoId(), 'tareas', task.id]);
        },
      },
    );
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
