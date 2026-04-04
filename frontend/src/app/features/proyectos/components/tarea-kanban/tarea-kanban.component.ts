/**
 * SaiSuite — TareaKanbanComponent
 * Vista Kanban de tareas con drag & drop CDK.
 * Las columnas representan los estados de tarea.
 * El estado se actualiza en el backend optimísticamente al soltar una tarjeta.
 */
import {
  ChangeDetectionStrategy, ChangeDetectorRef,
  Component, DestroyRef, OnInit, OutputEmitterRef, effect, inject, input, output, signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { map } from 'rxjs/operators';
import { TareaDialogComponent, TareaDialogResult } from '../tarea-dialog/tarea-dialog.component';
import { FormsModule } from '@angular/forms';
import { ProyectoService } from '../../services/proyecto.service';
import { ProyectoList } from '../../models/proyecto.model';
import { FaseService } from '../../services/fase.service';
import { FaseList } from '../../models/fase.model';
import { AdminService } from '../../../admin/services/admin.service';
import { AdminUser } from '../../../admin/models/admin.models';
import { AuthService } from '../../../../core/auth/auth.service';
import {
  CdkDragDrop, CdkDropList, CdkDrag, CdkDragPlaceholder, CdkDropListGroup,
  moveItemInArray, transferArrayItem,
} from '@angular/cdk/drag-drop';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { MatDialog } from '@angular/material/dialog';
import { TareaService } from '../../services/tarea.service';
import { TareaCardComponent } from '../tarea-card/tarea-card.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { Tarea, TareaEstado, TareaFilters } from '../../models/tarea.model';
import { ToastService } from '../../../../core/services/toast.service';

interface KanbanColumn {
  id: TareaEstado;
  nombre: string;
  color: string;
  tareas: Tarea[];
}

const COLUMNAS_DEF: Omit<KanbanColumn, 'tareas'>[] = [
  { id: 'todo',   nombre: 'Por Hacer',   color: '#9e9e9e' },
  { id: 'in_progress', nombre: 'En Progreso', color: '#1e88e5' },
  { id: 'in_review', nombre: 'En Revisión', color: '#fb8c00' },
  { id: 'blocked',   nombre: 'Bloqueada',   color: '#e53935' },
  { id: 'completed',  nombre: 'Completada',  color: '#43a047' },
];

interface SelectOption { label: string; value: number | null; }

@Component({
  selector: 'app-tarea-kanban',
  templateUrl: './tarea-kanban.component.html',
  styleUrl: './tarea-kanban.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, FormsModule,
    CdkDropListGroup, CdkDropList, CdkDrag, CdkDragPlaceholder,
    MatButtonModule, MatIconModule,
    MatInputModule, MatFormFieldModule, MatSelectModule,
    MatProgressBarModule, MatTooltipModule, MatDividerModule,
    TareaCardComponent,
  ],
})
export class TareaKanbanComponent implements OnInit {
  private readonly tareaService    = inject(TareaService);
  private readonly router          = inject(Router);
  private readonly route           = inject(ActivatedRoute);
  private readonly dialog          = inject(MatDialog);
  private readonly toast           = inject(ToastService);
  private readonly cdr             = inject(ChangeDetectorRef);
  private readonly destroyRef      = inject(DestroyRef);
  private readonly proyectoService = inject(ProyectoService);
  private readonly faseService     = inject(FaseService);
  private readonly adminService    = inject(AdminService);
  private readonly authService     = inject(AuthService);

  /**
   * Input para uso embebido (ej: tab dentro de proyecto-detail).
   * Tiene prioridad sobre el query param ?proyecto= de la ruta.
   */
  readonly proyectoIdInput = input<string | null>(null);

  /**
   * Emite cuando el usuario pulsa "Lista" en modo embebido.
   * El componente padre gestiona el cambio de vista sin navegar.
   */
  readonly listaToggled: OutputEmitterRef<void> = output<void>();

  readonly loading          = signal(false);
  readonly searchText       = signal('');
  readonly prioridadFilter  = signal<number | null>(null);
  readonly proyectoFilter   = signal<string | null>(null);
  readonly responsableFilter = signal<string | null>(null);

  // Datos para los dropdowns de filtro
  readonly proyectos = signal<ProyectoList[]>([]);
  readonly fases     = signal<FaseList[]>([]);
  readonly usuarios  = signal<AdminUser[]>([]);
  readonly faseFilter = signal<string | null>(null);

  /** true cuando la vista se abrió desde "Mis Tareas" */
  readonly esMisTareas = signal(false);

  /** Conservado para compatibilidad con nuevaTarea() */
  private get proyectoId(): string | null { return this.proyectoFilter(); }

  constructor() {
    // Reaccionar a cambios del input proyectoIdInput (modo embebido).
    effect(() => {
      const inputId = this.proyectoIdInput();
      if (inputId !== null) {
        this.proyectoFilter.set(inputId);
        this.faseFilter.set(null);
        this.loadFasesByProyecto(inputId);
        this.loadTareas();
      }
    });
  }

  /** Estado mutable (no signal) porque CDK muta los arrays in-place. */
  columnas: KanbanColumn[] = COLUMNAS_DEF.map(d => ({ ...d, tareas: [] }));

  readonly prioridadOptions: SelectOption[] = [
    { label: 'Todas las prioridades', value: null },
    { label: 'Baja',    value: 1 },
    { label: 'Normal',  value: 2 },
    { label: 'Alta',    value: 3 },
    { label: 'Urgente', value: 4 },
  ];

  get totalTareas(): number {
    return this.columnas.reduce((sum, c) => sum + c.tareas.length, 0);
  }

  ngOnInit(): void {
    localStorage.setItem('saisuite.tareasView', 'kanban');

    this.loadProyectos();
    this.loadUsuarios();

    const inputId = this.proyectoIdInput();

    // Suscribirse al observable para reaccionar cuando cambian los query params
    // (mismo componente, distinto param: Tareas ↔ Mis Tareas)
    this.route.queryParamMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(params => {
        const esMis = params.get('mis_tareas') === '1';
        this.esMisTareas.set(esMis);

        // Ajustar filtro de responsable según contexto
        if (esMis) {
          this.responsableFilter.set('mis-tareas');
        } else if (this.responsableFilter() === 'mis-tareas') {
          // Venía de mis-tareas y ahora es tareas generales: limpiar
          this.responsableFilter.set(null);
        }

        // El input tiene prioridad sobre el query param (modo embebido vs. ruta directa).
        const pid = inputId ?? params.get('proyecto');
        if (pid && pid !== this.proyectoFilter()) {
          this.proyectoFilter.set(pid);
          this.loadFasesByProyecto(pid);
        }

        // Solo cargar aquí cuando no hay inputId (el effect maneja el modo embebido)
        if (!inputId) {
          this.loadTareas();
        }

        // Auto-abrir modal si la URL contiene ?tarea=<uuid>
        const tid = params.get('tarea');
        if (tid) this.abrirDialog(tid);
      });
  }

  private loadProyectos(): void {
    this.proyectoService.list({ page_size: 100, activo: true })
      .pipe(map(r => r.results))
      .subscribe({
        next: (proyectos) => this.proyectos.set(proyectos),
        error: () => { /* silencioso — los filtros siguen funcionando */ },
      });
  }

  private loadUsuarios(): void {
    this.adminService.listUsers().subscribe({
      next: (res) => this.usuarios.set(res.results),
      error: () => { /* silencioso */ },
    });
  }

  private loadFasesByProyecto(proyectoId: string): void {
    this.faseService.listByProyecto(proyectoId).subscribe({
      next: (fases) => this.fases.set(fases),
      error: () => { /* silencioso */ },
    });
  }

  loadTareas(): void {
    this.loading.set(true);
    const filters: TareaFilters = {};

    if (this.proyectoFilter())   filters.proyecto  = this.proyectoFilter()!;
    if (this.faseFilter())       filters.fase      = this.faseFilter()!;
    if (this.prioridadFilter())  filters.prioridad = this.prioridadFilter() as 1|2|3|4;
    if (this.searchText())       filters.search    = this.searchText();

    const resp = this.responsableFilter();
    if (resp === 'mis-tareas') {
      filters.solo_mis_tareas = true;
    } else if (resp) {
      filters.responsable = resp;
    }

    this.tareaService.list(filters).subscribe({
      next: (tareas) => {
        this.distribuir(tareas);
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.toast.error('No se pudieron cargar las tareas.');
        this.loading.set(false);
      },
    });
  }

  private distribuir(tareas: Tarea[]): void {
    // Resetear cada columna sin crear nuevas referencias de array (CDK las trackea)
    this.columnas.forEach(c => { c.tareas = []; });
    tareas.forEach(t => {
      const col = this.columnas.find(c => c.id === t.estado);
      if (col) col.tareas.push(t);
    });
  }

  onDrop(event: CdkDragDrop<Tarea[]>, targetCol: KanbanColumn): void {
    if (event.previousContainer === event.container) {
      // Reorden dentro de la misma columna
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
      this.cdr.markForCheck();
      return;
    }

    const tarea = event.previousContainer.data[event.previousIndex];

    // Actualización optimista en UI
    transferArrayItem(
      event.previousContainer.data,
      event.container.data,
      event.previousIndex,
      event.currentIndex,
    );
    this.cdr.markForCheck();

    // Persistir en backend
    this.tareaService.cambiarEstado(tarea.id, targetCol.id).subscribe({
      next: () => {
        this.toast.success(`Tarea movida a "${targetCol.nombre}".`);
      },
      error: (err: { error?: { detail?: string } }) => {
        // Revertir cambio optimista
        transferArrayItem(
          event.container.data,
          event.previousContainer.data,
          event.currentIndex,
          event.previousIndex,
        );
        this.cdr.markForCheck();
        const msg = err.error?.detail ?? 'No se pudo mover la tarea.';
        this.toast.error(msg);
      },
    });
  }

  nuevaTarea(): void {
    const pid = this.proyectoFilter();
    const inputId = this.proyectoIdInput();
    const queryParams: Record<string, string> = {};
    if (pid) queryParams['proyecto'] = pid;
    if (inputId) queryParams['returnTo'] = `proyecto:${inputId}:tab:5`;
    this.router.navigate(['/proyectos/tareas/nueva'], { queryParams });
  }

  limpiarFiltros(): void {
    this.searchText.set('');
    this.proyectoFilter.set(null);
    this.faseFilter.set(null);
    this.fases.set([]);
    this.responsableFilter.set(null);
    this.prioridadFilter.set(null);
    this.loadTareas();
  }

  get hayFiltrosActivos(): boolean {
    return !!(this.searchText() || this.proyectoFilter() || this.faseFilter() || this.responsableFilter() || this.prioridadFilter());
  }

  editarTarea(tarea: Tarea): void {
    const inputId = this.proyectoIdInput();
    const extras = inputId
      ? { queryParams: { returnTo: `proyecto:${inputId}:tab:5` } }
      : {};
    this.router.navigate(['/proyectos/tareas', tarea.id, 'editar'], extras);
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
      if (confirmed) this.eliminar(tarea);
    });
  }

  private eliminar(tarea: Tarea): void {
    this.tareaService.delete(tarea.id).subscribe({
      next: () => {
        const col = this.columnas.find(c => c.id === tarea.estado);
        if (col) {
          col.tareas = col.tareas.filter(t => t.id !== tarea.id);
          this.cdr.markForCheck();
        }
        this.toast.success('Tarea eliminada correctamente.');
      },
      error: () => this.toast.error('No se pudo eliminar la tarea.'),
    });
  }

  verDetalle(tarea: Tarea): void {
    this.abrirDialog(tarea.id);
  }

  private abrirDialog(tareaId: string): void {
    // Añadir ?tarea= a la URL para que sea linkeable/recargar
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tarea: tareaId },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });

    const ref = this.dialog.open<TareaDialogComponent, unknown, TareaDialogResult>(
      TareaDialogComponent,
      {
        data: { tareaId },
        width: '820px',
        height: '88vh',
        maxWidth: '96vw',
        maxHeight: '96vh',
        panelClass: 'trd-dialog-panel',
      },
    );

    ref.afterClosed().subscribe((result) => {
      if (result?.navigateTo) {
        this.router.navigate(result.navigateTo!, {
          queryParams: result.navigateParams,
        });
        return;
      }

      // Limpiar el query param ?tarea= de la URL
      this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { tarea: null },
        queryParamsHandling: 'merge',
        replaceUrl: true,
      });

      // Si el estado cambió, recargar el tablero
      if (result?.updated) {
        this.loadTareas();
      }
    });
  }

  onProgressUpdate(event: { tarea: Tarea; progreso: number }): void {
    this.tareaService.update(event.tarea.id, { porcentaje_completado: event.progreso }).subscribe({
      next: (updated) => {
        // Actualizar el objeto en la columna (mutación in-place, mismo patrón que CDK)
        event.tarea.porcentaje_completado = updated.porcentaje_completado;
        this.cdr.markForCheck();
        this.toast.success('Progreso actualizado.');
      },
      error: () => this.toast.error('No se pudo actualizar el progreso.'),
    });
  }

  onTimeRegister(tarea: Tarea): void {
    this.abrirDialog(tarea.id);
  }

  onSearch(): void    { this.loadTareas(); }
  onFilter(): void    { this.loadTareas(); }
  onFaseChange(id: string | null): void     { this.faseFilter.set(id);      this.loadTareas(); }
  onResponsableChange(v: string | null): void { this.responsableFilter.set(v); this.loadTareas(); }

  onProyectoChange(id: string | null): void {
    this.proyectoFilter.set(id);
    this.faseFilter.set(null);
    if (id) {
      this.loadFasesByProyecto(id);
    } else {
      this.fases.set([]);
    }
    this.loadTareas();
  }
  irALista(): void {
    localStorage.setItem('saisuite.tareasView', 'list');
    if (this.proyectoIdInput()) {
      // Modo embebido: notificar al padre para que cambie la vista sin navegar
      this.listaToggled.emit();
      return;
    }
    const returnTo = this.route.snapshot.queryParamMap.get('returnTo');
    if (returnTo?.startsWith('proyecto:')) {
      const proyectoId = returnTo.slice('proyecto:'.length);
      this.router.navigate(['/proyectos', proyectoId]);
      return;
    }
    const route = this.esMisTareas() ? '/proyectos/mis-tareas' : '/proyectos/tareas';
    this.router.navigate([route]);
  }
}
