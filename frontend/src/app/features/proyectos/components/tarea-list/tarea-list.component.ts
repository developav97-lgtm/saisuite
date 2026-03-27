/**
 * SaiSuite — TareaListComponent
 * Lista de tareas con filtros server-side, paginación client-side y acciones CRUD.
 */
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { TareaService } from '../../services/tarea.service';
import { Tarea, TareaEstado, TareaPrioridad, TareaFilters } from '../../models/tarea.model';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

export const ESTADO_LABELS: Record<string, string> = {
  todo:        'Por Hacer',
  in_progress: 'En Progreso',
  in_review:   'En Revisión',
  blocked:     'Bloqueada',
  completed:   'Completada',
  cancelled:   'Cancelada',
};

export const PRIORIDAD_LABELS: Record<string, string> = {
  1: 'Baja',
  2: 'Normal',
  3: 'Alta',
  4: 'Urgente',
};

interface SelectOption<T> { label: string; value: T; }

@Component({
  selector: 'app-tarea-list',
  templateUrl: './tarea-list.component.html',
  styleUrl: './tarea-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, FormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatInputModule, MatFormFieldModule, MatSelectModule,
    MatPaginatorModule, MatProgressBarModule, MatTooltipModule,
  ],
})
export class TareaListComponent implements OnInit {
  private readonly tareaService = inject(TareaService);
  private readonly router       = inject(Router);
  private readonly route        = inject(ActivatedRoute);
  private readonly dialog       = inject(MatDialog);
  private readonly snackBar     = inject(MatSnackBar);

  readonly tareas         = signal<Tarea[]>([]);
  readonly totalCount     = signal(0);
  readonly loading        = signal(false);
  readonly searchText     = signal('');
  readonly estadoFilter   = signal<TareaEstado | null>(null);
  readonly prioridadFilter = signal<TareaPrioridad | null>(null);
  /** Preseleccionado desde query param cuando se llega desde proyecto-detail. */
  readonly proyectoId     = signal<string | null>(null);

  readonly pageSize = 25;

  readonly displayedColumns = [
    'codigo', 'nombre', 'responsable', 'estado', 'prioridad',
    'porcentaje', 'fecha_limite', 'acciones',
  ];

  readonly estadoOptions: SelectOption<TareaEstado | null>[] = [
    { label: 'Todos los estados', value: null },
    ...Object.entries(ESTADO_LABELS).map(([value, label]) => ({
      label,
      value: value as TareaEstado,
    })),
  ];

  readonly prioridadOptions: SelectOption<TareaPrioridad | null>[] = [
    { label: 'Todas las prioridades', value: null },
    { label: 'Baja',    value: 1 },
    { label: 'Normal',  value: 2 },
    { label: 'Alta',    value: 3 },
    { label: 'Urgente', value: 4 },
  ];

  readonly ESTADO_LABELS   = ESTADO_LABELS;
  readonly PRIORIDAD_LABELS = PRIORIDAD_LABELS;

  ngOnInit(): void {
    const pid = this.route.snapshot.queryParamMap.get('proyecto');
    if (pid) this.proyectoId.set(pid);
    this.loadTareas();
  }

  loadTareas(): void {
    this.loading.set(true);
    const filters: TareaFilters = {};
    if (this.proyectoId())     filters.proyecto  = this.proyectoId()!;
    if (this.estadoFilter())   filters.estado    = this.estadoFilter()!;
    if (this.prioridadFilter()) filters.prioridad = this.prioridadFilter()!;
    if (this.searchText())     filters.search    = this.searchText();

    this.tareaService.list(filters).subscribe({
      next: (tareas) => {
        this.tareas.set(tareas);
        this.totalCount.set(tareas.length);
        this.loading.set(false);
      },
      error: () => {
        this.snackBar.open('No se pudieron cargar las tareas.', 'Cerrar', {
          duration: 4000, panelClass: ['snack-error'],
        });
        this.loading.set(false);
      },
    });
  }

  onSearch(): void       { this.loadTareas(); }
  onFilterChange(): void { this.loadTareas(); }
  onPage(_event: PageEvent): void { /* paginación client-side vía mat-paginator */ }
  irAKanban(): void      { this.router.navigate(['/proyectos/tareas/kanban']); }

  nuevaTarea(): void {
    const extras = this.proyectoId()
      ? { queryParams: { proyecto: this.proyectoId() } }
      : {};
    this.router.navigate(['/proyectos/tareas/nueva'], extras);
  }

  verDetalle(id: string): void {
    this.router.navigate(['/proyectos/tareas', id], {
      queryParams: { returnTo: 'list' },
    });
  }
  editarTarea(id: string): void { this.router.navigate(['/proyectos/tareas', id, 'editar']); }

  confirmarEliminar(tarea: Tarea): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header:      'Eliminar tarea',
        message:     `¿Eliminar la tarea "${tarea.nombre}"? Esta acción no se puede deshacer.`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
      width: '420px',
    });
    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) this.eliminar(tarea.id);
    });
  }

  private eliminar(id: string): void {
    this.tareaService.delete(id).subscribe({
      next: () => {
        this.snackBar.open('Tarea eliminada correctamente.', 'Cerrar', {
          duration: 3000, panelClass: ['snack-success'],
        });
        this.loadTareas();
      },
      error: () => this.snackBar.open('No se pudo eliminar la tarea.', 'Cerrar', {
        duration: 4000, panelClass: ['snack-error'],
      }),
    });
  }

  estadoClass(estado: TareaEstado): string {
    return `tl-estado-badge tl-estado-badge--${estado}`;
  }

  prioridadClass(prioridad: number): string {
    return `tl-prioridad-badge tl-prioridad-badge--${prioridad}`;
  }

  formatDate(date: string | null): string {
    if (!date) return '—';
    return new Date(date + 'T00:00:00').toLocaleDateString('es-CO');
  }
}
