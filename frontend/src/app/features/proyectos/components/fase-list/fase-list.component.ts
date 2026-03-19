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
import { MatSnackBar } from '@angular/material/snack-bar';
import { FaseService } from '../../services/fase.service';
import { FaseList, FaseDetail } from '../../models/fase.model';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

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
  ],
})
export class FaseListComponent implements OnInit {
  private readonly faseService = inject(FaseService);
  private readonly fb          = inject(FormBuilder);
  private readonly dialog      = inject(MatDialog);
  private readonly snackBar    = inject(MatSnackBar);

  readonly proyectoId          = input.required<string>();
  readonly presupuestoProyecto = input<string>('0');

  readonly fases        = signal<FaseList[]>([]);
  readonly loading      = signal(false);
  readonly editingFase  = signal<FaseDetail | null>(null);

  readonly displayedColumns = ['orden', 'nombre', 'presupuesto', 'avance', 'acciones'];

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
    porcentaje_avance:        [0],
  });

  ngOnInit(): void { this.loadFases(); }

  loadFases(): void {
    this.loading.set(true);
    this.faseService.listByProyecto(this.proyectoId()).subscribe({
      next: (fases) => { this.fases.set(fases); this.loading.set(false); },
      error: () => { this.loading.set(false); },
    });
  }

  abrirDialogNueva(): void {
    this.editingFase.set(null);
    this.form.reset({
      presupuesto_mano_obra: 0, presupuesto_materiales: 0,
      presupuesto_subcontratos: 0, presupuesto_equipos: 0,
      presupuesto_otros: 0, porcentaje_avance: 0,
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
          porcentaje_avance:        parseFloat(detail.porcentaje_avance        || '0'),
        });
        this.syncBudgetDisplays();
        this.dialogRef = this.dialog.open(this.faseFormTemplate, {
          width: 'min(760px, 95vw)', maxHeight: '90vh',
        });
      },
      error: () => {
        this.snackBar.open('No se pudo cargar la fase.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
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
      porcentaje_avance:        (val.porcentaje_avance        ?? 0).toString(),
    };

    const editing = this.editingFase();
    const obs = editing
      ? this.faseService.update(editing.id, payload)
      : this.faseService.create(this.proyectoId(), payload);
    obs.subscribe({
      next: () => {
        this.dialogRef?.close();
        this.loadFases();
        this.snackBar.open(`Fase ${editing ? 'actualizada' : 'creada'} correctamente.`, 'Cerrar', { duration: 3000, panelClass: ['snack-success'] });
      },
      error: (err) => {
        const e = err as { error?: unknown };
        let detail = 'Error al guardar la fase.';
        if (Array.isArray(e.error)) detail = e.error[0] as string;
        this.snackBar.open(detail, 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
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
          this.snackBar.open('Fase eliminada.', 'Cerrar', { duration: 3000, panelClass: ['snack-success'] });
        },
      });
    });
  }

  presupuestoTotal(fase: FaseList): number { return parseFloat(fase.presupuesto_total || '0'); }
  presupuestoProyectoNum(): number { return parseFloat(this.presupuestoProyecto() || '0'); }
  presupuestoTotalFases(): number { return this.fases().reduce((sum, f) => sum + this.presupuestoTotal(f), 0); }
  formatCurrency(value: number): string { return value.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }); }
}
