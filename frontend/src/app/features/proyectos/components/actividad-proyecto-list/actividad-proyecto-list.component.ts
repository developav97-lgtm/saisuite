import {
  ChangeDetectionStrategy, Component, OnInit, TemplateRef, ViewChild,
  computed, inject, input, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActividadProyectoService } from '../../services/actividad-proyecto.service';
import { ActividadService } from '../../services/actividad.service';
import { ActividadProyecto, ActividadList, TipoActividad, TIPO_ACTIVIDAD_LABELS } from '../../models/actividad.model';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-actividad-proyecto-list',
  templateUrl: './actividad-proyecto-list.component.html',
  styleUrl: './actividad-proyecto-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatCardModule, MatProgressSpinnerModule, MatProgressBarModule,
    MatTooltipModule, MatDialogModule,
  ],
})
export class ActividadProyectoListComponent implements OnInit {
  private readonly apService       = inject(ActividadProyectoService);
  private readonly actividadService = inject(ActividadService);
  private readonly fb              = inject(FormBuilder);
  private readonly dialog          = inject(MatDialog);
  private readonly snackBar        = inject(MatSnackBar);

  readonly proyectoId     = input.required<string>();
  readonly proyectoEstado = input<string>('');

  readonly asignaciones     = signal<ActividadProyecto[]>([]);
  readonly catalogo         = signal<ActividadList[]>([]);
  readonly loading          = signal(false);
  readonly saving           = signal(false);
  readonly editingAp        = signal<ActividadProyecto | null>(null);

  /** Cantidad ejecutada solo es editable si el proyecto está en ejecución o suspendido. */
  readonly puedeEjecutar = computed(() =>
    ['en_ejecucion', 'suspendido'].includes(this.proyectoEstado())
  );

  readonly displayedColumns = ['actividad', 'tipo', 'unidad', 'cantidad', 'costo', 'presupuesto', 'avance', 'acciones'];
  readonly TIPO_LABELS = TIPO_ACTIVIDAD_LABELS;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  @ViewChild('apFormTpl') apFormTemplate!: TemplateRef<any>;
  private dialogRef: MatDialogRef<unknown> | null = null;

  readonly form = this.fb.group({
    actividad:            ['', Validators.required],
    cantidad_planificada: [null as number | null, [Validators.required, Validators.min(0)]],
    cantidad_ejecutada:   [0],
    costo_unitario:       [null as number | null],
  });

  ngOnInit(): void {
    this.loadAsignaciones();
    this.loadCatalogo();
  }

  loadAsignaciones(): void {
    this.loading.set(true);
    this.apService.listByProyecto(this.proyectoId()).subscribe({
      next: (data) => { this.asignaciones.set(data); this.loading.set(false); },
      error: () => { this.loading.set(false); },
    });
  }

  loadCatalogo(): void {
    this.actividadService.list(undefined, undefined, 1, 500).subscribe({
      next: (res) => this.catalogo.set(res.results),
    });
  }

  abrirDialogAsignar(): void {
    this.editingAp.set(null);
    this.form.reset({ cantidad_ejecutada: 0 });
    if (!this.puedeEjecutar()) {
      this.form.get('cantidad_ejecutada')?.disable();
    } else {
      this.form.get('cantidad_ejecutada')?.enable();
    }
    this.dialogRef = this.dialog.open(this.apFormTemplate, {
      width: 'min(580px, 95vw)', maxHeight: '90vh',
    });
  }

  abrirDialogEditar(ap: ActividadProyecto): void {
    this.editingAp.set(ap);
    this.form.patchValue({
      actividad:            ap.actividad,
      cantidad_planificada: parseFloat(ap.cantidad_planificada || '0'),
      cantidad_ejecutada:   parseFloat(ap.cantidad_ejecutada || '0'),
      costo_unitario:       parseFloat(ap.costo_unitario || '0'),
    });
    // actividad no editable en modo edición
    this.form.get('actividad')?.disable();
    if (!this.puedeEjecutar()) {
      this.form.get('cantidad_ejecutada')?.disable();
    } else {
      this.form.get('cantidad_ejecutada')?.enable();
    }
    this.dialogRef = this.dialog.open(this.apFormTemplate, {
      width: 'min(580px, 95vw)', maxHeight: '90vh',
    });
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const val = this.form.getRawValue();

    const payload = {
      actividad:            val.actividad ?? '',
      cantidad_planificada: (val.cantidad_planificada ?? 0).toString(),
      cantidad_ejecutada:   (val.cantidad_ejecutada ?? 0).toString(),
      costo_unitario:       val.costo_unitario != null ? val.costo_unitario.toString() : undefined,
    };

    const editing = this.editingAp();
    const obs = editing
      ? this.apService.update(this.proyectoId(), editing.id, payload)
      : this.apService.asignar(this.proyectoId(), payload);

    obs.subscribe({
      next: () => {
        this.saving.set(false);
        this.form.get('actividad')?.enable();
        this.form.get('cantidad_ejecutada')?.enable();
        this.dialogRef?.close();
        this.loadAsignaciones();
        this.snackBar.open(
          `Actividad ${editing ? 'actualizada' : 'asignada'} correctamente.`,
          'Cerrar',
          { duration: 3000, panelClass: ['snack-success'] },
        );
      },
      error: (err) => {
        this.saving.set(false);
        this.form.get('actividad')?.enable();
        this.form.get('cantidad_ejecutada')?.enable();
        const e = err as { error?: Record<string, string[]> };
        const firstError = e.error ? Object.values(e.error).flat()[0] : null;
        this.snackBar.open(firstError ?? 'Error al guardar.', 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
      },
    });
  }

  onCancelar(): void {
    this.form.get('actividad')?.enable();
    this.form.get('cantidad_ejecutada')?.enable();
    this.dialogRef?.close();
  }

  confirmarDesasignar(ap: ActividadProyecto): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header:      'Confirmar',
        message:     `¿Quitar la actividad "${ap.actividad_codigo} — ${ap.actividad_nombre}" de este proyecto?`,
        acceptLabel: 'Quitar',
        acceptColor: 'warn',
      },
      width: '420px',
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.apService.desasignar(this.proyectoId(), ap.id).subscribe({
        next: () => {
          this.loadAsignaciones();
          this.snackBar.open('Actividad quitada del proyecto.', 'Cerrar', { duration: 3000, panelClass: ['snack-success'] });
        },
      });
    });
  }

  presupuestoTotal(): number {
    return this.asignaciones().reduce((sum, ap) => sum + parseFloat(ap.presupuesto_total || '0'), 0);
  }

  getTipoLabel(tipo: string): string {
    return TIPO_ACTIVIDAD_LABELS[tipo as TipoActividad] ?? tipo;
  }

  formatCurrency(value: string | number): string {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return num.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
  }
}
