import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  signal,
  inject,
  computed,
} from '@angular/core';
import { ReactiveFormsModule, FormBuilder } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSnackBar } from '@angular/material/snack-bar';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

import {
  ContabilidadService,
  MovimientoContable,
  GLFiltros,
} from '../../services/contabilidad.service';

const TITULOS = [
  { value: '', label: 'Todos' },
  { value: '1', label: '1 — Activo' },
  { value: '2', label: '2 — Pasivo' },
  { value: '3', label: '3 — Patrimonio' },
  { value: '4', label: '4 — Ingresos' },
  { value: '5', label: '5 — Gastos' },
  { value: '6', label: '6 — Costos' },
];

@Component({
  selector: 'app-gl-viewer-page',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatCardModule,
    MatTableModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatChipsModule,
    MatPaginatorModule,
  ],
  templateUrl: './gl-viewer-page.component.html',
  styleUrl: './gl-viewer-page.component.scss',
})
export class GlViewerPageComponent implements OnInit {
  private readonly svc = inject(ContabilidadService);
  private readonly fb  = inject(FormBuilder);
  private readonly snackBar = inject(MatSnackBar);

  readonly titulos = TITULOS;

  readonly loading     = signal(false);
  readonly movimientos = signal<MovimientoContable[]>([]);
  readonly totalCount  = signal(0);
  readonly pageIndex   = signal(0);
  readonly pageSize    = signal(25);
  readonly pageSizeOptions = [10, 25, 50, 100];

  readonly totalDebito = computed(() =>
    this.movimientos().reduce((acc, m) => acc + parseFloat(m.debito || '0'), 0)
  );
  readonly totalCredito = computed(() =>
    this.movimientos().reduce((acc, m) => acc + parseFloat(m.credito || '0'), 0)
  );
  readonly balanceado = computed(() =>
    Math.abs(this.totalDebito() - this.totalCredito()) < 1
  );
  readonly isEmpty = computed(() =>
    !this.loading() && this.movimientos().length === 0
  );

  readonly displayedColumns = [
    'fecha', 'auxiliar', 'tercero_nombre', 'descripcion', 'tipo', 'debito', 'credito',
  ];

  readonly form = this.fb.group({
    periodo:       [''],
    titulo_codigo: [''],
    search:        [''],
    fecha_inicio:  [''],
    fecha_fin:     [''],
  });

  ngOnInit(): void {
    this.cargar(this.buildFiltros(this.form.value));
    this.form.valueChanges.pipe(
      debounceTime(400),
      distinctUntilChanged((a, b) => JSON.stringify(a) === JSON.stringify(b)),
    ).subscribe(v => {
      this.pageIndex.set(0);
      this.cargar(this.buildFiltros(v));
    });
  }

  cargar(filtros: GLFiltros): void {
    this.loading.set(true);
    const withPaging: GLFiltros = {
      ...filtros,
      page: this.pageIndex() + 1,
      page_size: this.pageSize(),
    };
    this.svc.getMovimientos(withPaging).subscribe({
      next: res => {
        this.movimientos.set(res.results);
        this.totalCount.set(res.count);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open(
          'Error al cargar movimientos contables. Intenta nuevamente.',
          'Cerrar',
          { panelClass: 'sc-snackbar-error', duration: 5000 },
        );
      },
    });
  }

  onPage(e: PageEvent): void {
    this.pageIndex.set(e.pageIndex);
    this.pageSize.set(e.pageSize);
    this.cargar(this.buildFiltros(this.form.value));
  }

  limpiar(): void {
    this.form.reset({ periodo: '', titulo_codigo: '', search: '', fecha_inicio: '', fecha_fin: '' });
    this.pageIndex.set(0);
  }

  private buildFiltros(v: typeof this.form.value): GLFiltros {
    const f: GLFiltros = {};
    if (v.periodo)       f.periodo = v.periodo ?? undefined;
    if (v.titulo_codigo) f.titulo_codigo = v.titulo_codigo ?? undefined;
    if (v.search)        f.search = v.search ?? undefined;
    if (v.fecha_inicio)  f.fecha_inicio = v.fecha_inicio ?? undefined;
    if (v.fecha_fin)     f.fecha_fin = v.fecha_fin ?? undefined;
    return f;
  }

  formatMoney(value: string | number): string {
    const n = typeof value === 'string' ? parseFloat(value) : value;
    if (!n) return '—';
    return new Intl.NumberFormat('es-CO', {
      style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0,
    }).format(n);
  }
}
