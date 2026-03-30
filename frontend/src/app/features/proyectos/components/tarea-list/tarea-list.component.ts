/**
 * SaiSuite — TareaListComponent
 * Lista de tareas con filtros server-side, paginación client-side y acciones CRUD.
 * Soporta modo "Mis Tareas" cuando la ruta lleva data.misTareas = true.
 */
import { AfterViewInit, ChangeDetectionStrategy, Component, DestroyRef, OnInit, OutputEmitterRef, ViewChild, effect, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSortModule, MatSort } from '@angular/material/sort';
import { MatDialog } from '@angular/material/dialog';
import { TareaService } from '../../services/tarea.service';
import { Tarea, TareaEstado, TareaPrioridad, TareaFilters } from '../../models/tarea.model';
import { FaseService } from '../../services/fase.service';
import { FaseList } from '../../models/fase.model';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../core/services/toast.service';
import { HasPermissionDirective } from '../../../../core/directives/has-permission.directive';

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
    MatSortModule, HasPermissionDirective,
  ],
})
export class TareaListComponent implements OnInit, AfterViewInit {
  private readonly tareaService = inject(TareaService);
  private readonly faseService  = inject(FaseService);
  private readonly router       = inject(Router);
  private readonly route        = inject(ActivatedRoute);
  private readonly dialog       = inject(MatDialog);
  private readonly toast       = inject(ToastService);
  private readonly destroyRef   = inject(DestroyRef);

  /**
   * Input para uso embebido (ej: tab dentro de proyecto-detail).
   * Tiene prioridad sobre el query param ?proyecto= de la ruta.
   */
  readonly proyectoIdInput = input<string | null>(null);

  /**
   * Cuando se provee, los botones "Kanban" y "Nueva tarea" navegan con
   * returnTo=proyecto:<id> para que el formulario sepa a dónde volver.
   */
  readonly returnProyectoId = input<string | null>(null);

  /**
   * Emite cuando el usuario pulsa "Kanban" en modo embebido (returnProyectoId está seteado).
   * El componente padre gestiona el cambio de vista sin navegar.
   */
  readonly kanbanToggled: OutputEmitterRef<void> = output<void>();

  readonly tareas          = signal<Tarea[]>([]);
  readonly totalCount      = signal(0);

  readonly dataSource = new MatTableDataSource<Tarea>([]);
  @ViewChild(MatSort) sort!: MatSort;
  readonly loading         = signal(false);
  readonly searchText      = signal('');
  readonly estadoFilter    = signal<TareaEstado | null>(null);
  readonly prioridadFilter = signal<TareaPrioridad | null>(null);
  readonly faseFilter      = signal<string | null>(null);
  /** Preseleccionado desde query param o desde proyectoIdInput. */
  readonly proyectoId      = signal<string | null>(null);
  /** true cuando la ruta tiene data.misTareas = true */
  readonly esMisTareas     = signal(false);
  /** Lista de fases disponibles para el selector (se carga cuando hay proyectoId) */
  readonly fases           = signal<FaseList[]>([]);

  readonly pageSize = 25;

  constructor() {
    // Reaccionar a cambios del input proyectoIdInput (modo embebido).
    // allowSignalWrites: true permite que el effect actualice signals derivados.
    effect(() => {
      const inputId = this.proyectoIdInput();
      if (inputId !== null) {
        this.proyectoId.set(inputId);
        this.loadFases(inputId);
        this.loadTareas();
      }
    }, { allowSignalWrites: true });

    // Sincronizar el signal de tareas con MatTableDataSource para el sort.
    effect(() => {
      this.dataSource.data = this.tareas();
    });
  }

  ngAfterViewInit(): void {
    this.dataSource.sort = this.sort;
  }

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
    // Detectar modo "Mis Tareas" desde route data
    const routeData = this.route.snapshot.data;
    if (routeData['misTareas'] === true) {
      this.esMisTareas.set(true);
    }

    // El input tiene prioridad; si no hay input, leer el query param de la ruta.
    const inputId = this.proyectoIdInput();
    const pid = inputId ?? this.route.snapshot.queryParamMap.get('proyecto');
    if (pid) {
      this.proyectoId.set(pid);
      this.loadFases(pid);
    }

    // Solo cargar aquí cuando no hay inputId: el effect() maneja el caso embebido
    // para evitar una carga duplicada en la inicialización.
    if (!inputId) {
      this.loadTareas();
    }
  }

  private loadFases(proyectoId: string): void {
    this.faseService.listByProyecto(proyectoId).subscribe({
      next: (fases) => this.fases.set(fases),
      error: () => { /* silencioso: el filtro de fase simplemente no muestra opciones */ },
    });
  }

  loadTareas(): void {
    this.loading.set(true);
    const filters: TareaFilters = {};
    if (this.proyectoId())      filters.proyecto       = this.proyectoId()!;
    if (this.estadoFilter())    filters.estado         = this.estadoFilter()!;
    if (this.prioridadFilter()) filters.prioridad      = this.prioridadFilter()!;
    if (this.faseFilter())      filters.fase           = this.faseFilter()!;
    if (this.searchText())      filters.search         = this.searchText();
    if (this.esMisTareas())     filters.solo_mis_tareas = true;

    this.tareaService.list(filters).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (tareas) => {
        this.tareas.set(tareas);
        this.totalCount.set(tareas.length);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('No se pudieron cargar las tareas.');
        this.loading.set(false);
      },
    });
  }

  onSearch(): void       { this.loadTareas(); }
  onFilterChange(): void { this.loadTareas(); }
  onPage(_event: PageEvent): void { /* paginación client-side vía mat-paginator */ }
  irAKanban(): void {
    localStorage.setItem('saisuite.tareasView', 'kanban');
    const returnId = this.returnProyectoId();
    if (returnId) {
      // Modo embebido: notificar al padre para que cambie la vista sin navegar
      this.kanbanToggled.emit();
      return;
    }
    const extras = this.esMisTareas()
      ? { queryParams: { mis_tareas: '1' } }
      : {};
    this.router.navigate(['/proyectos/tareas/kanban'], extras);
  }

  nuevaTarea(): void {
    const returnId = this.returnProyectoId();
    const pid = returnId ?? this.proyectoId();
    const queryParams: Record<string, string> = {};
    if (pid) queryParams['proyecto'] = pid;
    if (returnId) queryParams['returnTo'] = `proyecto:${returnId}:tab:5`;
    this.router.navigate(['/proyectos/tareas/nueva'], { queryParams });
  }

  verDetalle(id: string): void {
    this.router.navigate(['/proyectos/tareas', id], {
      queryParams: { returnTo: 'list' },
    });
  }
  editarTarea(id: string): void {
    const returnId = this.returnProyectoId();
    const extras = returnId
      ? { queryParams: { returnTo: `proyecto:${returnId}:tab:5` } }
      : {};
    this.router.navigate(['/proyectos/tareas', id, 'editar'], extras);
  }

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
        this.toast.success('Tarea eliminada correctamente.');
        this.loadTareas();
      },
      error: () => this.toast.error('No se pudo eliminar la tarea.'),
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
