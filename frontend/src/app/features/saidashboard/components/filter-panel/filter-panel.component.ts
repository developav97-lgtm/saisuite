import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  effect,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import { ReportService } from '../../services/report.service';
import {
  ReportFilter,
  FilterTercero,
  FilterProyecto,
  FilterDepartamento,
  FilterPeriodo,
} from '../../models/report-filter.model';

@Component({
  selector: 'app-filter-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatSlideToggleModule,
    MatButtonModule,
    MatIconModule,
    MatAutocompleteModule,
    MatExpansionModule,
    MatChipsModule,
    MatTooltipModule,
  ],
  templateUrl: './filter-panel.component.html',
  styleUrl: './filter-panel.component.scss',
})
export class FilterPanelComponent implements OnInit {
  private readonly reportService = inject(ReportService);
  private readonly destroyRef = inject(DestroyRef);

  /** Filtros guardados del dashboard. Se cargan al abrir. */
  readonly savedFilter = input<ReportFilter | null>(null);
  /** Controla si el panel empieza expandido (default: true). Usar false en el builder. */
  readonly startExpanded = input<boolean>(true);

  readonly filterChange = output<ReportFilter>();
  /** Emitido cuando el usuario quiere guardar los filtros actuales como predeterminados */
  readonly saveAsDefault = output<ReportFilter>();

  // ── State ──────────────────────────────────────────────────
  readonly fechaDesde = signal<Date | null>(null);
  readonly fechaHasta = signal<Date | null>(null);
  readonly selectedTercero = signal<FilterTercero | null>(null);
  readonly selectedProyecto = signal<string | null>(null);
  readonly selectedDepartamento = signal<string | null>(null);
  readonly selectedPeriodo = signal<string | null>(null);
  readonly compararPeriodo = signal(false);
  readonly expanded = signal(true);

  /** Si true, retorna serie mensual de 12 barras */
  readonly agruparPorMes = signal(false);
  /** Año para la serie mensual */
  readonly anio = signal<string | null>(null);

  /** True cuando los filtros actuales difieren de los guardados */
  readonly hasPendingChanges = signal(false);

  /** Indica si los filtros guardados ya fueron cargados (para no recargar en cada cambio) */
  private _savedFilterLoaded = false;

  // Autocomplete
  readonly terceroSearch = new FormControl('');
  readonly terceroOptions = signal<FilterTercero[]>([]);

  // Dropdown options
  readonly proyectos = signal<FilterProyecto[]>([]);
  readonly departamentos = signal<FilterDepartamento[]>([]);
  readonly periodos = signal<FilterPeriodo[]>([]);

  // Años disponibles extraidos de periodos
  readonly aniosDisponibles = computed(() => {
    const set = new Set<string>();
    for (const p of this.periodos()) {
      const anio = (p.periodo ?? '').slice(0, 4);
      if (anio) set.add(anio);
    }
    return Array.from(set).sort().reverse();
  });

  // Active filter count for collapsed badge
  readonly activeFilterCount = computed(() => {
    let count = 0;
    if (this.fechaDesde() || this.fechaHasta()) count++; // rango de fechas = 1 filtro
    if (this.selectedTercero()) count++;
    if (this.selectedProyecto()) count++;
    if (this.selectedDepartamento()) count++;
    if (this.selectedPeriodo()) count++;
    if (this.agruparPorMes()) count++;
    return count;
  });

  constructor() {
    // Carga el savedFilter cuando llega (una sola vez)
    effect(() => {
      const saved = this.savedFilter();
      if (saved && !this._savedFilterLoaded) {
        this._savedFilterLoaded = true;
        this._loadFromFilter(saved);
      }
    });
  }

  ngOnInit(): void {
    this.expanded.set(this.startExpanded());
    this.loadFilterOptions();
    this.setupTerceroAutocomplete();
  }

  private loadFilterOptions(): void {
    this.reportService.getProyectos()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(p => this.proyectos.set(p));

    this.reportService.getDepartamentos()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(d => this.departamentos.set(d));

    this.reportService.getPeriodos()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(p => this.periodos.set(p));
  }

  private setupTerceroAutocomplete(): void {
    this.terceroSearch.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => this.reportService.searchTerceros(q ?? '')),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(results => this.terceroOptions.set(results));
  }

  /** Carga los valores de un ReportFilter en las señales del panel */
  private _loadFromFilter(filter: ReportFilter): void {
    this.fechaDesde.set(filter.fecha_desde ? new Date(filter.fecha_desde) : null);
    this.fechaHasta.set(filter.fecha_hasta ? new Date(filter.fecha_hasta) : null);
    this.selectedProyecto.set(filter.proyecto_codigo ?? null);
    this.selectedDepartamento.set(filter.departamento_codigo ?? null);
    this.selectedPeriodo.set(filter.periodo ?? null);
    this.compararPeriodo.set(filter.comparar_periodo ?? false);
    this.agruparPorMes.set(filter.agrupar_por_mes ?? false);
    this.anio.set(filter.anio ?? null);
    // Tercero: carga solo el id; la UI mostrara el autocomplete vacío
    if (filter.tercero_id) {
      this.selectedTercero.set({ id: filter.tercero_id, nombre: filter.tercero_id });
    }
    this.emitFilter();
  }

  // ── Quick period buttons ───────────────────────────────────
  setQuickPeriod(period: 'month' | 'quarter' | 'year' | 'last_year'): void {
    const now = new Date();
    let desde: Date;
    let hasta: Date;

    switch (period) {
      case 'month':
        desde = new Date(now.getFullYear(), now.getMonth(), 1);
        hasta = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        break;
      case 'quarter': {
        const q = Math.floor(now.getMonth() / 3);
        desde = new Date(now.getFullYear(), q * 3, 1);
        hasta = new Date(now.getFullYear(), q * 3 + 3, 0);
        break;
      }
      case 'year':
        desde = new Date(now.getFullYear(), 0, 1);
        hasta = new Date(now.getFullYear(), 11, 31);
        break;
      case 'last_year':
        desde = new Date(now.getFullYear() - 1, 0, 1);
        hasta = new Date(now.getFullYear() - 1, 11, 31);
        break;
    }

    this.fechaDesde.set(desde);
    this.fechaHasta.set(hasta);
    this.emitFilter();
  }

  onTerceroSelected(tercero: FilterTercero): void {
    this.selectedTercero.set(tercero);
    this.emitFilter();
  }

  clearTercero(): void {
    this.selectedTercero.set(null);
    this.terceroSearch.setValue('');
    this.emitFilter();
  }

  displayTercero(tercero: FilterTercero): string {
    return tercero?.nombre ?? '';
  }

  applyFilters(): void {
    this.emitFilter();
  }

  clearAll(): void {
    this.fechaDesde.set(null);
    this.fechaHasta.set(null);
    this.selectedTercero.set(null);
    this.selectedProyecto.set(null);
    this.selectedDepartamento.set(null);
    this.selectedPeriodo.set(null);
    this.compararPeriodo.set(false);
    this.agruparPorMes.set(false);
    this.anio.set(null);
    this.terceroSearch.setValue('');
    this.emitFilter();
  }

  onSaveAsDefault(): void {
    const filter = this._buildFilter();
    this.saveAsDefault.emit(filter);
    // Marcamos como sin cambios pendientes
    this.hasPendingChanges.set(false);
  }

  emitFilter(): void {
    const filter = this._buildFilter();
    this.filterChange.emit(filter);
    this._checkPendingChanges(filter);
  }

  private _buildFilter(): ReportFilter {
    const desde = this.fechaDesde();
    const hasta = this.fechaHasta();
    return {
      fecha_desde: desde ? this.formatDate(desde) : null,
      fecha_hasta: hasta ? this.formatDate(hasta) : null,
      tercero_id: this.selectedTercero()?.id ?? null,
      proyecto_codigo: this.selectedProyecto() ?? null,
      departamento_codigo: this.selectedDepartamento() ?? null,
      periodo: this.selectedPeriodo() ?? null,
      comparar_periodo: this.compararPeriodo(),
      agrupar_por_mes: this.agruparPorMes(),
      anio: this.anio() ?? null,
    };
  }

  private _checkPendingChanges(current: ReportFilter): void {
    const saved = this.savedFilter();
    if (!saved) {
      this.hasPendingChanges.set(false);
      return;
    }
    const equal = JSON.stringify(current) === JSON.stringify(saved);
    this.hasPendingChanges.set(!equal);
  }

  private formatDate(d: Date): string {
    return d.toISOString().split('T')[0];
  }
}
