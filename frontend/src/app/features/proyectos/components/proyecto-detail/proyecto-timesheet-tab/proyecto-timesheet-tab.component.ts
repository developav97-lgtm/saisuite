/**
 * SaiSuite — ProyectoTimesheetTabComponent
 * Tab de timesheets del proyecto: lista todas las entradas de horas registradas
 * por el equipo, filtradas por proyecto, con paginación client-side y total.
 */
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  inject,
  input,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TimesheetService } from '../../../services/timesheet.service';
import { TimesheetEntry } from '../../../models/timesheet.model';
import { ToastService } from '../../../../../core/services/toast.service';

@Component({
  selector: 'app-proyecto-timesheet-tab',
  templateUrl: './proyecto-timesheet-tab.component.html',
  styleUrl: './proyecto-timesheet-tab.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatTableModule,
    MatPaginatorModule,
    MatProgressBarModule,
    MatIconModule,
    MatTooltipModule,
  ],
})
export class ProyectoTimesheetTabComponent {
  private readonly timesheetService = inject(TimesheetService);
  private readonly toast       = inject(ToastService);

  readonly proyectoId = input.required<string>();

  readonly allTimesheets = signal<TimesheetEntry[]>([]);
  readonly loading       = signal(false);
  readonly pageIndex     = signal(0);
  readonly pageSize      = signal(25);

  readonly totalItems = computed(() => this.allTimesheets().length);

  readonly totalHoras = computed(() =>
    this.allTimesheets().reduce((sum, e) => sum + e.horas, 0),
  );

  readonly pagedTimesheets = computed(() => {
    const start = this.pageIndex() * this.pageSize();
    return this.allTimesheets().slice(start, start + this.pageSize());
  });

  readonly displayedColumns = ['fecha', 'usuario', 'tarea', 'horas', 'descripcion'];

  constructor() {
    effect(() => {
      const id = this.proyectoId();
      if (id) {
        this.loadTimesheets(id);
      }
    });
  }

  loadTimesheets(proyectoId: string): void {
    this.loading.set(true);
    this.pageIndex.set(0);
    this.timesheetService.listByProyecto(proyectoId).subscribe({
      next: (entries) => {
        this.allTimesheets.set(entries);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('No se pudieron cargar los timesheets.');
        this.loading.set(false);
      },
    });
  }

  onPage(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
  }

  formatDate(date: string): string {
    return new Date(date + 'T00:00:00').toLocaleDateString('es-CO');
  }

  formatHoras(horas: number | string): string {
    return `${Number(horas).toFixed(1)} h`;
  }
}
