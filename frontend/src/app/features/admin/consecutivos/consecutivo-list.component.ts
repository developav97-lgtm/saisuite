import {
  ChangeDetectionStrategy, Component, OnInit, TemplateRef, ViewChild,
  computed, inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ConsecutivoService, ConsecutivoParams } from '../services/consecutivo.service';
import {
  ConsecutivoConfig, ConsecutivoCreate, EntidadConsecutivo,
  ENTIDAD_LABELS, FORMATO_OPCIONES, SUBTIPOS_POR_ENTIDAD,
} from '../models/consecutivo.model';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-consecutivo-list',
  templateUrl: './consecutivo-list.component.html',
  styleUrl: './consecutivo-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule, FormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatSlideToggleModule,
    MatProgressBarModule, MatProgressSpinnerModule,
    MatTooltipModule, MatDialogModule, MatPaginatorModule,
  ],
})
export class ConsecutivoListComponent implements OnInit {
  private readonly service  = inject(ConsecutivoService);
  private readonly fb       = inject(FormBuilder);
  private readonly dialog   = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);

  readonly consecutivos  = signal<ConsecutivoConfig[]>([]);
  readonly searchText    = signal('');
  readonly filtroTipo    = signal<EntidadConsecutivo | ''>('');
  readonly filtroActivo  = signal<string>('all');
  readonly totalCount    = signal(0);
  readonly currentPage   = signal(1);
  readonly pageSize      = 25;

  readonly hayFiltros = computed(() =>
    !!this.searchText() || !!this.filtroTipo() || this.filtroActivo() !== 'all',
  );

  readonly loading       = signal(false);
  readonly saving        = signal(false);
  readonly editing       = signal<ConsecutivoConfig | null>(null);
  readonly formatPreview = signal('');

  readonly selectedTipo   = signal<EntidadConsecutivo | null>(null);
  readonly subtipOpciones = computed(() =>
    this.selectedTipo() ? (SUBTIPOS_POR_ENTIDAD[this.selectedTipo()!] ?? []) : [],
  );

  readonly displayedColumns = ['tipo', 'nombre', 'prefijo', 'proximo_codigo', 'formato', 'activo', 'acciones'];

  readonly entidadOpciones: { value: EntidadConsecutivo; label: string }[] = [
    { value: 'proyecto',  label: 'Proyecto'  },
    { value: 'actividad', label: 'Actividad' },
    { value: 'factura',   label: 'Factura'   },
  ];

  readonly estadoOpciones = [
    { value: 'all',   label: 'Todos'    },
    { value: 'true',  label: 'Activo'   },
    { value: 'false', label: 'Inactivo' },
  ];

  readonly formatoOpciones = FORMATO_OPCIONES;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  @ViewChild('formTpl') formTemplate!: TemplateRef<any>;
  private dialogRef: MatDialogRef<unknown> | null = null;

  readonly form = this.fb.group({
    nombre:        ['', [Validators.required, Validators.maxLength(100)]],
    tipo:          [null as EntidadConsecutivo | null, Validators.required],
    subtipo:       [''],
    prefijo:       ['', [Validators.required, Validators.maxLength(20)]],
    ultimo_numero: [0, [Validators.required, Validators.min(0)]],
    formato:       ['{prefijo}-{numero:04d}', Validators.required],
    activo:        [true],
  });

  ngOnInit(): void {
    this.loadConsecutivos();
    this.form.get('tipo')?.valueChanges.subscribe(v => {
      this.selectedTipo.set(v as EntidadConsecutivo | null);
      this.form.get('subtipo')?.setValue('');
    });
    this.form.get('prefijo')?.valueChanges.subscribe(() => this.updatePreview());
    this.form.get('formato')?.valueChanges.subscribe(() => this.updatePreview());
  }

  loadConsecutivos(): void {
    this.loading.set(true);
    const params: ConsecutivoParams = {
      page:      this.currentPage(),
      page_size: this.pageSize,
      search:    this.searchText() || undefined,
      tipo:      this.filtroTipo() || undefined,
      activo:    this.filtroActivo() !== 'all' ? this.filtroActivo() : undefined,
    };
    this.service.list(params).subscribe({
      next: (data) => {
        this.consecutivos.set(data.results ?? []);
        this.totalCount.set(data.count ?? 0);
        this.loading.set(false);
      },
      error: () => {
        this.snackBar.open('No se pudieron cargar los consecutivos.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
        this.loading.set(false);
      },
    });
  }

  onSearch(): void {
    this.currentPage.set(1);
    this.loadConsecutivos();
  }

  aplicarFiltros(): void {
    this.currentPage.set(1);
    this.loadConsecutivos();
  }

  limpiarFiltros(): void {
    this.searchText.set('');
    this.filtroTipo.set('');
    this.filtroActivo.set('all');
    this.currentPage.set(1);
    this.loadConsecutivos();
  }

  onPageChange(event: PageEvent): void {
    this.currentPage.set(event.pageIndex + 1);
    this.loadConsecutivos();
  }

  updatePreview(): void {
    const { prefijo, formato } = this.form.getRawValue();
    if (!prefijo || !formato) { this.formatPreview.set(''); return; }
    try {
      const result = formato
        .replace('{prefijo}', prefijo)
        .replace(/\{numero(?::[^}]+)?\}/g, '0001');
      this.formatPreview.set(result);
    } catch {
      this.formatPreview.set('');
    }
  }

  abrirDialogNuevo(): void {
    this.editing.set(null);
    this.selectedTipo.set(null);
    this.form.reset({ formato: '{prefijo}-{numero:04d}', activo: true, ultimo_numero: 0 });
    this.formatPreview.set('');
    this.dialogRef = this.dialog.open(this.formTemplate, { width: 'min(520px, 95vw)', maxHeight: '90vh' });
  }

  abrirDialogEditar(cfg: ConsecutivoConfig): void {
    this.editing.set(cfg);
    this.selectedTipo.set(cfg.tipo);
    this.form.patchValue({
      nombre:        cfg.nombre,
      tipo:          cfg.tipo,
      subtipo:       cfg.subtipo,
      prefijo:       cfg.prefijo,
      ultimo_numero: cfg.ultimo_numero,
      formato:       cfg.formato,
      activo:        cfg.activo,
    });
    this.updatePreview();
    this.dialogRef = this.dialog.open(this.formTemplate, { width: 'min(520px, 95vw)', maxHeight: '90vh' });
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const val = this.form.getRawValue();
    const payload: ConsecutivoCreate = {
      nombre:        val.nombre ?? '',
      tipo:          val.tipo as EntidadConsecutivo,
      subtipo:       val.subtipo ?? '',
      prefijo:       val.prefijo ?? '',
      ultimo_numero: val.ultimo_numero ?? 0,
      formato:       val.formato ?? '{prefijo}-{numero:04d}',
      activo:        val.activo ?? true,
    };

    const cfg = this.editing();
    const obs = cfg
      ? this.service.update(cfg.id, payload)
      : this.service.create(payload);

    obs.subscribe({
      next: () => {
        this.saving.set(false);
        this.dialogRef?.close();
        this.loadConsecutivos();
        this.snackBar.open(
          `Consecutivo ${cfg ? 'actualizado' : 'creado'} correctamente.`,
          'Cerrar',
          { duration: 3000, panelClass: ['snack-success'] },
        );
      },
      error: (err) => {
        this.saving.set(false);
        const e = err as { error?: Record<string, string[]> };
        const msg = e.error ? Object.values(e.error).flat()[0] : 'Error al guardar.';
        this.snackBar.open(msg ?? 'Error al guardar.', 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
      },
    });
  }

  confirmarEliminar(cfg: ConsecutivoConfig): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header:      'Confirmar eliminación',
        message:     `¿Eliminar el consecutivo "${cfg.nombre}" (${cfg.prefijo})?`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
      width: '420px',
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.service.delete(cfg.id).subscribe({
        next: () => {
          this.loadConsecutivos();
          this.snackBar.open('Consecutivo eliminado.', 'Cerrar', { duration: 3000, panelClass: ['snack-success'] });
        },
      });
    });
  }

  getEntidadLabel(tipo: string): string {
    return ENTIDAD_LABELS[tipo as EntidadConsecutivo] ?? tipo;
  }

  getFormatoLabel(formato: string): string {
    return FORMATO_OPCIONES.find(o => o.value === formato)?.label ?? formato;
  }
}
