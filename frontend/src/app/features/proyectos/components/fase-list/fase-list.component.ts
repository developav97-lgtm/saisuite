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
  imports: [
    CommonModule, ReactiveFormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule,
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

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  @ViewChild('faseFormTpl') faseFormTemplate!: TemplateRef<any>;
  private dialogRef: MatDialogRef<unknown> | null = null;

  readonly form = this.fb.group({
    nombre:                   ['', Validators.required],
    descripcion:              [''],
    orden:                    [null as number | null],
    fecha_inicio_planificada: ['', Validators.required],
    fecha_fin_planificada:    ['', Validators.required],
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
    this.form.reset({ presupuesto_mano_obra: 0, presupuesto_materiales: 0, presupuesto_subcontratos: 0, presupuesto_equipos: 0, presupuesto_otros: 0, porcentaje_avance: 0 });
    this.dialogRef = this.dialog.open(this.faseFormTemplate, { width: '640px', disableClose: false });
  }

  abrirDialogEditar(fase: FaseList): void {
    this.faseService.listByProyecto(this.proyectoId()).subscribe({
      next: (fases) => {
        const detail = fases.find(f => f.id === fase.id) as unknown as FaseDetail;
        if (detail) {
          this.editingFase.set(detail);
          this.form.patchValue({
            nombre: detail.nombre, descripcion: detail.descripcion, orden: detail.orden,
            fecha_inicio_planificada: detail.fecha_inicio_planificada,
            fecha_fin_planificada: detail.fecha_fin_planificada,
            presupuesto_mano_obra: parseFloat(detail.presupuesto_mano_obra || '0'),
            presupuesto_materiales: parseFloat(detail.presupuesto_materiales || '0'),
            presupuesto_subcontratos: parseFloat(detail.presupuesto_subcontratos || '0'),
            presupuesto_equipos: parseFloat(detail.presupuesto_equipos || '0'),
            presupuesto_otros: parseFloat(detail.presupuesto_otros || '0'),
            porcentaje_avance: parseFloat(detail.porcentaje_avance || '0'),
          });
          this.dialogRef = this.dialog.open(this.faseFormTemplate, { width: '640px' });
        }
      },
    });
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const val = this.form.getRawValue();
    const payload = {
      nombre: val.nombre!, descripcion: val.descripcion || '',
      orden: val.orden ?? undefined,
      fecha_inicio_planificada: val.fecha_inicio_planificada!,
      fecha_fin_planificada: val.fecha_fin_planificada!,
      presupuesto_mano_obra:    val.presupuesto_mano_obra?.toString() ?? '0',
      presupuesto_materiales:   val.presupuesto_materiales?.toString() ?? '0',
      presupuesto_subcontratos: val.presupuesto_subcontratos?.toString() ?? '0',
      presupuesto_equipos:      val.presupuesto_equipos?.toString() ?? '0',
      presupuesto_otros:        val.presupuesto_otros?.toString() ?? '0',
      porcentaje_avance:        val.porcentaje_avance?.toString() ?? '0',
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
