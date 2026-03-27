import {
  ChangeDetectionStrategy, Component, OnInit, TemplateRef, ViewChild,
  computed, inject, input, signal, OnDestroy,
} from '@angular/core';
import { Subscription } from 'rxjs';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormsModule } from '@angular/forms';
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
    CommonModule, ReactiveFormsModule, FormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatCardModule, MatProgressSpinnerModule, MatProgressBarModule,
    MatTooltipModule, MatDialogModule,
  ],
})
export class ActividadProyectoListComponent implements OnInit, OnDestroy {
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
  readonly costoDisplay     = signal('');

  /** Cantidad ejecutada siempre deshabilitada — se calcula automáticamente desde tareas. */
  readonly puedeEjecutar = computed(() =>
    ['in_progress', 'suspended'].includes(this.proyectoEstado())
  );

  /** Eliminar actividades solo permitido en estado borrador. */
  readonly puedeEliminar = computed(() =>
    !['planned', 'in_progress'].includes(this.proyectoEstado())
  );

  private actividadSub?: Subscription;

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
    // Auto-fill costo_unitario al seleccionar actividad (P1)
    this.actividadSub = this.form.get('actividad')!.valueChanges.subscribe(actId => {
      if (!actId || this.editingAp()) return;
      const act = this.catalogo().find(a => a.id === actId);
      if (act) {
        const costo = parseFloat(act.costo_unitario_base || '0');
        this.form.get('costo_unitario')!.setValue(costo, { emitEvent: false });
        this.costoDisplay.set(costo > 0 ? costo.toLocaleString('es-CO') : '');
      }
    });
  }

  ngOnDestroy(): void {
    this.actividadSub?.unsubscribe();
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
    this.costoDisplay.set('');
    this.form.reset({ cantidad_ejecutada: 0 });
    // cantidad_ejecutada siempre calculada automáticamente desde tareas (P3)
    this.form.get('cantidad_ejecutada')?.disable();
    this.dialogRef = this.dialog.open(this.apFormTemplate, {
      width: 'min(580px, 95vw)', maxHeight: '90vh',
    });
  }

  abrirDialogEditar(ap: ActividadProyecto): void {
    this.editingAp.set(ap);
    const costo = parseFloat(ap.costo_unitario || '0');
    this.form.patchValue({
      actividad:            ap.actividad,
      cantidad_planificada: parseFloat(ap.cantidad_planificada || '0'),
      cantidad_ejecutada:   parseFloat(ap.cantidad_ejecutada || '0'),
      costo_unitario:       costo,
    });
    this.costoDisplay.set(costo > 0 ? costo.toLocaleString('es-CO') : '');
    // actividad y cantidad_ejecutada no editables en modo edición (P3)
    this.form.get('actividad')?.disable();
    this.form.get('cantidad_ejecutada')?.disable();
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
        const e = err as { error?: Record<string, string[]> };
        const firstError = e.error ? Object.values(e.error).flat()[0] : null;
        this.snackBar.open(firstError ?? 'Error al guardar.', 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
      },
    });
  }

  onCancelar(): void {
    this.form.get('actividad')?.enable();
    this.dialogRef?.close();
  }

  // ── Formato costo unitario (P2) ─────────────────────────────
  onCostoInput(event: Event): void {
    const raw    = (event.target as HTMLInputElement).value;
    const digits = raw.replace(/[^0-9]/g, '');
    const num    = digits ? parseInt(digits, 10) : 0;
    this.form.get('costo_unitario')!.setValue(num, { emitEvent: false });
    this.costoDisplay.set(digits ? num.toLocaleString('es-CO') : '');
  }

  onCostoFocus(): void {
    const val = this.form.get('costo_unitario')?.value ?? 0;
    this.costoDisplay.set(val > 0 ? String(val) : '');
  }

  onCostoBlur(): void {
    const val = this.form.get('costo_unitario')?.value ?? 0;
    this.costoDisplay.set(val > 0 ? (val as number).toLocaleString('es-CO') : '');
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
