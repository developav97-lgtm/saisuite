import {
  ChangeDetectionStrategy, Component, OnInit, TemplateRef, ViewChild,
  computed, inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActividadService } from '../../services/actividad.service';
import { ActividadCreate, ActividadList, ActividadDetail, TipoActividad, TIPO_ACTIVIDAD_LABELS } from '../../models/actividad.model';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ConsecutivoService } from '../../../admin/services/consecutivo.service';
import { ConsecutivoConfig } from '../../../admin/models/consecutivo.model';

interface SelectOption { label: string; value: TipoActividad | null; }

const UNIDADES_MEDIDA = [
  'hora', 'día', 'semana', 'mes',
  'm²', 'm³', 'ml', 'km',
  'kg', 'ton', 'litro', 'galón',
  'unidad', 'global', 'viaje', 'jornal',
];

@Component({
  selector: 'app-actividad-list',
  templateUrl: './actividad-list.component.html',
  styleUrl: './actividad-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatAutocompleteModule,
    MatPaginatorModule, MatProgressBarModule, MatProgressSpinnerModule,
    MatTooltipModule, MatDialogModule,
  ],
})
export class ActividadListComponent implements OnInit {
  private readonly actividadService    = inject(ActividadService);
  private readonly consecutivoService  = inject(ConsecutivoService);
  private readonly fb                  = inject(FormBuilder);
  private readonly dialog              = inject(MatDialog);
  private readonly snackBar            = inject(MatSnackBar);

  readonly actividades      = signal<ActividadList[]>([]);
  readonly totalCount       = signal(0);
  readonly loading          = signal(false);
  readonly saving           = signal(false);
  readonly searchText       = signal('');
  readonly tipoFilter       = signal<TipoActividad | null>(null);
  readonly editingActividad = signal<ActividadDetail | null>(null);

  // Unidad de medida autocomplete
  readonly unidadInputText    = signal('');
  readonly unidadesFiltradas  = computed(() => {
    const txt = this.unidadInputText().toLowerCase().trim();
    if (!txt) return UNIDADES_MEDIDA;
    return UNIDADES_MEDIDA.filter(u => u.toLowerCase().includes(txt));
  });

  // Costo unitario display (formateado)
  readonly costoDisplay       = signal('');
  readonly allConsecutivos    = signal<ConsecutivoConfig[]>([]);
  readonly selectedTipoForm   = signal<TipoActividad | null>(null);

  // Filtra consecutivos de tipo='actividad' con subtipo = tipo seleccionado en el form
  readonly filteredConsecutivos = computed(() => {
    const tipo = this.selectedTipoForm();
    if (!tipo) return [];
    return this.allConsecutivos().filter(
      c => c.activo && c.tipo === 'actividad' && c.subtipo === tipo,
    );
  });
  readonly consecutivoUnico           = computed(() => { const l = this.filteredConsecutivos(); return l.length === 1 ? l[0] : null; });
  readonly mostrarSelectorConsecutivo = computed(() => this.filteredConsecutivos().length > 1);

  readonly pageSize = 25;
  readonly displayedColumns = ['codigo', 'nombre', 'tipo', 'unidad_medida', 'costo_unitario_base', 'acciones'];

  readonly tipoOptions: SelectOption[] = [
    { value: null,          label: 'Todos los tipos' },
    { value: 'mano_obra',   label: 'Mano de obra'    },
    { value: 'material',    label: 'Material'         },
    { value: 'equipo',      label: 'Equipo'           },
    { value: 'subcontrato', label: 'Subcontrato'      },
  ];

  readonly tipoOpciones = this.tipoOptions.filter(o => o.value !== null) as { value: TipoActividad; label: string }[];

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  @ViewChild('actividadFormTpl') actividadFormTemplate!: TemplateRef<any>;
  private dialogRef: MatDialogRef<unknown> | null = null;

  readonly form = this.fb.group({
    codigo:              [{ value: '', disabled: true }],
    consecutivo_id:      [null as string | null],
    nombre:              ['', Validators.required],
    descripcion:         [''],
    tipo:                ['' as TipoActividad, Validators.required],
    unidad_medida:       ['', Validators.required],
    costo_unitario_base: [0, [Validators.required, Validators.min(0)]],
  });

  ngOnInit(): void {
    this.loadActividades(0);
    // Cargar todos los consecutivos; filtrado por tipo via computed
    this.consecutivoService.list().subscribe({
      next: (list) => this.allConsecutivos.set(list),
      error: () => { /* silencioso */ },
    });
    // Actualizar selectedTipoForm al cambiar el tipo en el form
    this.form.get('tipo')?.valueChanges.subscribe(tipo => {
      this.selectedTipoForm.set(tipo as TipoActividad | null);
      const filtered = this.filteredConsecutivos();
      this.form.get('consecutivo_id')?.setValue(
        filtered.length === 1 ? filtered[0].id : null,
        { emitEvent: false },
      );
    });
  }

  loadActividades(pageIndex: number): void {
    this.loading.set(true);
    const search = this.searchText() || undefined;
    const tipo   = this.tipoFilter()  || undefined;
    this.actividadService.list(search, tipo, pageIndex + 1, this.pageSize).subscribe({
      next: (res) => {
        this.actividades.set(res.results);
        this.totalCount.set(res.count);
        this.loading.set(false);
      },
      error: () => {
        this.snackBar.open('No se pudieron cargar las actividades.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
        this.loading.set(false);
      },
    });
  }

  onSearch(): void           { this.loadActividades(0); }
  onFilterChange(): void     { this.loadActividades(0); }
  onPage(e: PageEvent): void { this.loadActividades(e.pageIndex); }

  // ── Unidad de medida autocomplete ──────────────────────────────
  onUnidadInput(event: Event): void {
    this.unidadInputText.set((event.target as HTMLInputElement).value);
  }

  // ── Costo unitario: formateo COP ───────────────────────────────
  onCostoInput(event: Event): void {
    const raw    = (event.target as HTMLInputElement).value;
    const digits = raw.replace(/[^0-9]/g, '');
    const num    = digits ? parseInt(digits, 10) : 0;
    this.form.get('costo_unitario_base')?.setValue(num, { emitEvent: false });
    // Muestra con separadores mientras escribe
    this.costoDisplay.set(digits ? num.toLocaleString('es-CO') : '');
  }

  onCostoFocus(): void {
    const val = this.form.get('costo_unitario_base')?.value ?? 0;
    this.costoDisplay.set(val > 0 ? val.toString() : '');
  }

  onCostoBlur(): void {
    const val = this.form.get('costo_unitario_base')?.value ?? 0;
    this.costoDisplay.set(val > 0 ? val.toLocaleString('es-CO') : '');
  }

  // ── Dialogs ────────────────────────────────────────────────────
  abrirDialogNueva(): void {
    this.editingActividad.set(null);
    this.selectedTipoForm.set(null);
    this.form.reset({ costo_unitario_base: 0, consecutivo_id: null });
    this.unidadInputText.set('');
    this.costoDisplay.set('');
    this.dialogRef = this.dialog.open(this.actividadFormTemplate, {
      width: 'min(560px, 95vw)', maxHeight: '90vh',
    });
  }

  abrirDialogEditar(actividad: ActividadList): void {
    this.actividadService.getById(actividad.id).subscribe({
      next: (detail) => {
        this.editingActividad.set(detail);
        const costo = parseFloat(detail.costo_unitario_base || '0');
        this.form.patchValue({
          codigo:              detail.codigo,
          nombre:              detail.nombre,
          descripcion:         detail.descripcion,
          tipo:                detail.tipo,
          unidad_medida:       detail.unidad_medida,
          costo_unitario_base: costo,
        });
        this.unidadInputText.set(detail.unidad_medida);
        this.costoDisplay.set(costo > 0 ? costo.toLocaleString('es-CO') : '');
        this.dialogRef = this.dialog.open(this.actividadFormTemplate, {
          width: 'min(560px, 95vw)', maxHeight: '90vh',
        });
      },
      error: () => {
        this.snackBar.open('No se pudo cargar la actividad.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
      },
    });
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const val = this.form.getRawValue();

    const editing = this.editingActividad();
    const payload: ActividadCreate = {
      ...(val.codigo ? { codigo: val.codigo } : {}),
      nombre:              val.nombre ?? '',
      descripcion:         val.descripcion ?? '',
      tipo:                val.tipo as TipoActividad,
      unidad_medida:       val.unidad_medida ?? '',
      costo_unitario_base: (val.costo_unitario_base ?? 0).toString(),
      // Solo al crear
      consecutivo_id: !editing ? (val.consecutivo_id ?? null) : undefined,
    };

    const obs = editing
      ? this.actividadService.update(editing.id, payload)
      : this.actividadService.create(payload);

    obs.subscribe({
      next: () => {
        this.saving.set(false);
        this.dialogRef?.close();
        this.loadActividades(0);
        this.snackBar.open(
          `Actividad ${editing ? 'actualizada' : 'creada'} correctamente.`,
          'Cerrar',
          { duration: 3000, panelClass: ['snack-success'] },
        );
      },
      error: (err) => {
        this.saving.set(false);
        const e = err as { error?: Record<string, string[]> };
        const firstError = e.error ? Object.values(e.error).flat()[0] : null;
        this.snackBar.open(firstError ?? 'Error al guardar la actividad.', 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
      },
    });
  }

  confirmarEliminar(actividad: ActividadList): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header:      'Confirmar eliminación',
        message:     `¿Eliminar la actividad "${actividad.codigo} — ${actividad.nombre}"? Esta acción no se puede deshacer.`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
      width: '400px',
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.actividadService.delete(actividad.id).subscribe({
        next: () => {
          this.loadActividades(0);
          this.snackBar.open('Actividad eliminada correctamente.', 'Cerrar', { duration: 3000, panelClass: ['snack-success'] });
        },
        error: (err) => {
          const e = err as { error?: string | Record<string, string[]> };
          const msg = typeof e.error === 'string' ? e.error : 'No se pudo eliminar la actividad.';
          this.snackBar.open(msg, 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
        },
      });
    });
  }

  getTipoLabel(tipo: string): string {
    return TIPO_ACTIVIDAD_LABELS[tipo as TipoActividad] ?? tipo;
  }

  formatCurrency(value: string): string {
    return parseFloat(value || '0').toLocaleString('es-CO', {
      style: 'currency', currency: 'COP', maximumFractionDigits: 0,
    });
  }
}
