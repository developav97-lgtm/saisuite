import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
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
  ],
  templateUrl: './filter-panel.component.html',
  styleUrl: './filter-panel.component.scss',
})
export class FilterPanelComponent implements OnInit {
  private readonly reportService = inject(ReportService);
  private readonly destroyRef = inject(DestroyRef);

  readonly filterChange = output<ReportFilter>();

  // ── State ──────────────────────────────────────────────────
  readonly fechaDesde = signal<Date | null>(null);
  readonly fechaHasta = signal<Date | null>(null);
  readonly selectedTercero = signal<FilterTercero | null>(null);
  readonly selectedProyecto = signal<string | null>(null);
  readonly selectedDepartamento = signal<string | null>(null);
  readonly selectedPeriodo = signal<string | null>(null);
  readonly compararPeriodo = signal(false);
  readonly expanded = signal(true);

  // Autocomplete
  readonly terceroSearch = new FormControl('');
  readonly terceroOptions = signal<FilterTercero[]>([]);

  // Dropdown options
  readonly proyectos = signal<FilterProyecto[]>([]);
  readonly departamentos = signal<FilterDepartamento[]>([]);
  readonly periodos = signal<FilterPeriodo[]>([]);

  // Active filter count for collapsed badge
  readonly activeFilterCount = computed(() => {
    let count = 0;
    if (this.fechaDesde()) count++;
    if (this.fechaHasta()) count++;
    if (this.selectedTercero()) count++;
    if (this.selectedProyecto()) count++;
    if (this.selectedDepartamento()) count++;
    if (this.selectedPeriodo()) count++;
    return count;
  });

  ngOnInit(): void {
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
    this.terceroSearch.setValue('');
    this.emitFilter();
  }

  private emitFilter(): void {
    const desde = this.fechaDesde();
    const hasta = this.fechaHasta();

    const filter: ReportFilter = {
      fecha_desde: desde ? this.formatDate(desde) : null,
      fecha_hasta: hasta ? this.formatDate(hasta) : null,
      tercero_id: this.selectedTercero()?.id ?? null,
      proyecto_codigo: this.selectedProyecto() ?? null,
      departamento_codigo: this.selectedDepartamento() ?? null,
      periodo: this.selectedPeriodo() ?? null,
      comparar_periodo: this.compararPeriodo(),
    };
    this.filterChange.emit(filter);
  }

  private formatDate(d: Date): string {
    return d.toISOString().split('T')[0];
  }
}
