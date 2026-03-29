import {
  ChangeDetectionStrategy, Component, OnInit, TemplateRef, ViewChild,
  inject, input, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { provideNativeDateAdapter } from '@angular/material/core';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { DragDropModule, CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { FaseService } from '../../services/fase.service';
import { FaseList, FaseDetail } from '../../models/fase.model';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-fase-list',
  templateUrl: './fase-list.component.html',
  styleUrl: './fase-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [provideNativeDateAdapter()],
  imports: [
    CommonModule, ReactiveFormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatDatepickerModule,
    MatProgressBarModule, MatTooltipModule, MatDialogModule,
    DragDropModule,
  ],
})
export class FaseListComponent implements OnInit {
  private readonly faseService = inject(FaseService);
  private readonly fb          = inject(FormBuilder);
  private readonly dialog      = inject(MatDialog);
  private readonly toast       = inject(ToastService);

  readonly proyectoId          = input.required<string>();
  readonly presupuestoProyecto = input<string>('0');

  readonly fases        = signal<FaseList[]>([]);
  readonly loading      = signal(false);
  readonly editingFase  = signal<FaseDetail | null>(null);
  readonly reordering   = signal(false);

  readonly displayedColumns = ['drag_handle', 'orden', 'nombre', 'estado', 'presupuesto', 'avance', 'acciones'];

  readonly budgetCats = [
    { key: 'presupuesto_mano_obra',    label: 'Mano de obra'  },
    { key: 'presupuesto_materiales',   label: 'Materiales'    },
    { key: 'presupuesto_subcontratos', label: 'Subcontratos'  },
    { key: 'presupuesto_equipos',      label: 'Equipos'       },
    { key: 'presupuesto_otros',        label: 'Otros'         },
  ];

  readonly budgetDisplays = signal<{ [key: string]: string }>({
    presupuesto_mano_obra: '0',    presupuesto_materiales: '0',
    presupuesto_subcontratos: '0', presupuesto_equipos: '0',
    presupuesto_otros: '0',
  });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  @ViewChild('faseFormTpl') faseFormTemplate!: TemplateRef<any>;
  private dialogRef: MatDialogRef<unknown> | null = null;

  readonly form = this.fb.group({
    nombre:                   ['', Validators.required],
    descripcion:              [''],
    orden:                    [null as number | null],
    fecha_inicio_planificada: [null as Date | null, Validators.required],
    fecha_fin_planificada:    [null as Date | null, Validators.required],
    presupuesto_mano_obra:    [0],
    presupuesto_materiales:   [0],
    presupuesto_subcontratos: [0],
    presupuesto_equipos:      [0],
    presupuesto_otros:        [0],
  });

  ngOnInit(): void { this.loadFases(); }

  loadFases(): void {
    this.loading.set(true);
    this.faseService.listByProyecto(this.proyectoId()).subscribe({
      next: (fases) => { this.fases.set(fases); this.loading.set(false); },
      error: () => { this.loading.set(false); },
    });
  }

  // ── Drag & Drop ──────────────────────────────────────────────────────────

  onDrop(event: CdkDragDrop<FaseList[]>): void {
    if (event.previousIndex === event.currentIndex) return;

    // Actualizar array local inmediatamente para UX fluida
    const fasesActuales = [...this.fases()];
    moveItemInArray(fasesActuales, event.previousIndex, event.currentIndex);
    this.fases.set(fasesActuales);

    // Recalcular orden: asignar posición 1-based según nuevo índice
    const fasesAfectadas = fasesActuales
      .map((f, idx) => ({ fase: f, nuevoOrden: idx + 1 }))
      .filter(({ fase, nuevoOrden }) => fase.orden !== nuevoOrden);

    if (fasesAfectadas.length === 0) return;

    this.reordering.set(true);

    // PATCH individual para cada fase cuyo orden cambió
    let pendientes = fasesAfectadas.length;
    let huboError = false;

    fasesAfectadas.forEach(({ fase, nuevoOrden }) => {
      this.faseService.update(fase.id, { orden: nuevoOrden }).subscribe({
        next: () => {
          pendientes--;
          if (pendientes === 0) {
            this.reordering.set(false);
            if (!huboError) {
              // Recargar para sincronizar con el backend
              this.loadFases();
            }
          }
        },
        error: () => {
          huboError = true;
          pendientes--;
          if (pendientes === 0) {
            this.reordering.set(false);
            this.toast.error('No se pudo reordenar las fases.');
            // Revertir al estado del servidor
            this.loadFases();
          }
        },
      });
    });
  }

  // ── CRUD ─────────────────────────────────────────────────────────────────

  abrirDialogNueva(): void {
    this.editingFase.set(null);
    this.form.reset({
      presupuesto_mano_obra: 0, presupuesto_materiales: 0,
      presupuesto_subcontratos: 0, presupuesto_equipos: 0,
      presupuesto_otros: 0,
      fecha_inicio_planificada: null, fecha_fin_planificada: null,
    });
    this.syncBudgetDisplays();
    this.dialogRef = this.dialog.open(this.faseFormTemplate, {
      width: 'min(760px, 95vw)', maxHeight: '90vh', disableClose: false,
    });
  }

  abrirDialogEditar(fase: FaseList): void {
    this.faseService.getById(fase.id).subscribe({
      next: (detail) => {
        this.editingFase.set(detail);
        this.form.patchValue({
          nombre: detail.nombre, descripcion: detail.descripcion, orden: detail.orden,
          fecha_inicio_planificada: detail.fecha_inicio_planificada
            ? new Date(detail.fecha_inicio_planificada + 'T00:00:00') : null,
          fecha_fin_planificada: detail.fecha_fin_planificada
            ? new Date(detail.fecha_fin_planificada + 'T00:00:00') : null,
          presupuesto_mano_obra:    parseFloat(detail.presupuesto_mano_obra    || '0'),
          presupuesto_materiales:   parseFloat(detail.presupuesto_materiales   || '0'),
          presupuesto_subcontratos: parseFloat(detail.presupuesto_subcontratos || '0'),
          presupuesto_equipos:      parseFloat(detail.presupuesto_equipos      || '0'),
          presupuesto_otros:        parseFloat(detail.presupuesto_otros        || '0'),
        });
        this.syncBudgetDisplays();
        this.dialogRef = this.dialog.open(this.faseFormTemplate, {
          width: 'min(760px, 95vw)', maxHeight: '90vh',
        });
      },
      error: () => {
        this.toast.error('No se pudo cargar la fase.');
      },
    });
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const val = this.form.getRawValue();

    const toIsoDate = (d: Date | null): string => {
      if (!d) return '';
      return [
        d.getFullYear(),
        String(d.getMonth() + 1).padStart(2, '0'),
        String(d.getDate()).padStart(2, '0'),
      ].join('-');
    };

    const payload = {
      nombre: val.nombre ?? '', descripcion: val.descripcion ?? '',
      orden: val.orden ?? undefined,
      fecha_inicio_planificada: toIsoDate(val.fecha_inicio_planificada),
      fecha_fin_planificada:    toIsoDate(val.fecha_fin_planificada),
      presupuesto_mano_obra:    (val.presupuesto_mano_obra    ?? 0).toString(),
      presupuesto_materiales:   (val.presupuesto_materiales   ?? 0).toString(),
      presupuesto_subcontratos: (val.presupuesto_subcontratos ?? 0).toString(),
      presupuesto_equipos:      (val.presupuesto_equipos      ?? 0).toString(),
      presupuesto_otros:        (val.presupuesto_otros        ?? 0).toString(),
    };

    const editing = this.editingFase();
    const obs = editing
      ? this.faseService.update(editing.id, payload)
      : this.faseService.create(this.proyectoId(), payload);
    obs.subscribe({
      next: () => {
        this.dialogRef?.close();
        this.loadFases();
        this.toast.success(`Fase ${editing ? 'actualizada' : 'creada'} correctamente.`);
      },
      error: (err) => {
        const e = err as { error?: unknown };
        let detail = 'Error al guardar la fase.';
        if (Array.isArray(e.error)) detail = e.error[0] as string;
        this.toast.error(detail);
      },
    });
  }

  onMonedaInput(key: string, event: Event): void {
    const raw = (event.target as HTMLInputElement).value.replace(/\D/g, '');
    const num = parseInt(raw || '0', 10);
    this.budgetDisplays.update(d => ({ ...d, [key]: num.toLocaleString('es-CO') }));
    this.form.get(key)?.setValue(num, { emitEvent: false });
  }

  private syncBudgetDisplays(): void {
    const val = this.form.getRawValue();
    this.budgetDisplays.set({
      presupuesto_mano_obra:    (val.presupuesto_mano_obra    ?? 0).toLocaleString('es-CO'),
      presupuesto_materiales:   (val.presupuesto_materiales   ?? 0).toLocaleString('es-CO'),
      presupuesto_subcontratos: (val.presupuesto_subcontratos ?? 0).toLocaleString('es-CO'),
      presupuesto_equipos:      (val.presupuesto_equipos      ?? 0).toLocaleString('es-CO'),
      presupuesto_otros:        (val.presupuesto_otros        ?? 0).toLocaleString('es-CO'),
    });
  }

  activarFase(fase: FaseList): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Activar fase',
        message: `¿Activar la fase "${fase.nombre}"? Esto desactivará cualquier otra fase activa del proyecto.`,
        acceptLabel: 'Activar',
        acceptColor: 'primary',
      },
      width: '420px',
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.faseService.activar(fase.id).subscribe({
        next: () => {
          this.loadFases();
          this.toast.success('Fase activada correctamente.');
        },
        error: (err) => {
          const e = err as { error?: { detail?: string } };
          const msg = e.error?.detail ?? 'No se pudo activar la fase.';
          this.toast.error(msg);
        },
      });
    });
  }

  completarFase(fase: FaseList): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Completar fase',
        message: `¿Marcar como completada la fase "${fase.nombre}"? Esta acción no se puede deshacer.`,
        acceptLabel: 'Completar',
        acceptColor: 'accent',
      },
      width: '420px',
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.faseService.completar(fase.id).subscribe({
        next: () => {
          this.loadFases();
          this.toast.success('Fase completada correctamente.');
        },
        error: (err) => {
          const e = err as { error?: { detail?: string } };
          const msg = e.error?.detail ?? 'No se pudo completar la fase.';
          this.toast.error(msg);
        },
      });
    });
  }

  readonly ESTADO_LABELS: Record<string, string> = {
    planned:   'Planificada',
    active:    'Activa',
    completed: 'Completada',
    cancelled: 'Cancelada',
  };

  confirmarEliminar(fase: FaseList): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: { header: 'Confirmar', message: `¿Eliminar la fase "${fase.nombre}"?`, acceptLabel: 'Eliminar', acceptColor: 'warn' },
      width: '400px',
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.faseService.delete(fase.id).subscribe({
        next: () => {
          this.loadFases();
          this.toast.success('Fase eliminada.');
        },
      });
    });
  }

  presupuestoTotal(fase: FaseList): number { return parseFloat(fase.presupuesto_total || '0'); }
  presupuestoProyectoNum(): number { return parseFloat(this.presupuestoProyecto() || '0'); }
  presupuestoTotalFases(): number { return this.fases().reduce((sum, f) => sum + this.presupuestoTotal(f), 0); }
  formatCurrency(value: number): string { return value.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }); }
}
