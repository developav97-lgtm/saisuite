import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  inject,
  input,
  output,
  signal,
  effect,
  computed,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatChipsModule, MatChipInputEvent } from '@angular/material/chips';
import { provideNativeDateAdapter } from '@angular/material/core';
import { ENTER, COMMA } from '@angular/cdk/keycodes';
import { debounceTime, distinctUntilChanged, Subject, switchMap } from 'rxjs';
import { map } from 'rxjs/operators';
import { BIFilterDef } from '../../models/bi-field.model';
import { ReportBIService } from '../../services/report-bi.service';

export interface FilterSelectOption {
  value: string;
  label: string;
}

@Component({
  selector: 'app-filter-builder',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [provideNativeDateAdapter()],
  imports: [
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatSelectModule,
    MatIconModule,
    MatButtonModule,
    MatAutocompleteModule,
    MatChipsModule,
  ],
  templateUrl: './filter-builder.component.html',
  styleUrl: './filter-builder.component.scss',
})
export class FilterBuilderComponent {
  private readonly reportBIService = inject(ReportBIService);
  private readonly destroyRef = inject(DestroyRef);

  readonly sources = input<string[]>([]);
  readonly filters = input<Record<string, unknown>>({});
  readonly layout = input<'sidebar' | 'horizontal'>('sidebar');
  readonly filtersChange = output<Record<string, unknown>>();

  readonly availableFilters = signal<BIFilterDef[]>([]);
  readonly filterOptions = signal<Record<string, FilterSelectOption[]>>({});

  /** Opciones filtradas en pantalla para autocomplete de terceros */
  readonly terceroOptions = signal<FilterSelectOption[]>([]);

  readonly chipSeparatorKeys = [ENTER, COMMA] as const;

  private lastSourceKey = '';
  private readonly terceroSearch$ = new Subject<string>();

  constructor() {
    effect(() => {
      const srcs = this.sources();
      const key = [...srcs].sort().join(',');
      if (srcs.length === 0) {
        this.availableFilters.set([]);
        this.filterOptions.set({});
        this.lastSourceKey = '';
      } else if (key !== this.lastSourceKey) {
        this.lastSourceKey = key;
        this.loadFilters(srcs);
      }
    });

    // Búsqueda de terceros con debounce
    this.terceroSearch$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => this.reportBIService.getFilterTerceros(q).pipe(
        map(res => res.map(t => ({
          value: t.id,
          label: t.nombre + (t.identificacion ? ` (${t.identificacion})` : ''),
        }))),
      )),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(opts => this.terceroOptions.set(opts));
  }

  private loadFilters(srcs: string[]): void {
    const allFilters: BIFilterDef[] = [];
    let pending = srcs.length;

    for (const src of srcs) {
      this.reportBIService.getFilters(src)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: filters => {
            for (const f of filters) {
              if (!allFilters.some(existing => existing.key === f.key)) {
                allFilters.push(f);
              }
            }
            pending--;
            if (pending === 0) {
              this.availableFilters.set(allFilters);
              this.loadOptionsBatch(allFilters, srcs[0]);
            }
          },
          error: () => { pending--; },
        });
    }
  }

  private loadOptionsBatch(filters: BIFilterDef[], source: string): void {
    const newOptions: Record<string, FilterSelectOption[]> = {};

    const loadMap: Record<string, () => void> = {
      periodos: () => {
        this.reportBIService.getFilterPeriodos()
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe(res => {
            newOptions['periodos'] = res.map(r => ({ value: r.periodo, label: r.periodo }));
            this.filterOptions.set({ ...this.filterOptions(), ...newOptions });
          });
      },
      proyecto_codigos: () => {
        this.reportBIService.getFilterProyectos()
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe(res => {
            newOptions['proyecto_codigos'] = res.map(r => ({
              value: r.proyecto_codigo,
              label: r.proyecto_nombre ? `${r.proyecto_codigo} - ${r.proyecto_nombre}` : r.proyecto_codigo,
            }));
            this.filterOptions.set({ ...this.filterOptions(), ...newOptions });
          });
      },
      departamento_codigos: () => {
        this.reportBIService.getFilterDepartamentos()
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe(res => {
            newOptions['departamento_codigos'] = res.map(r => ({
              value: r.departamento_codigo,
              label: r.departamento_nombre ? `${r.departamento_codigo} - ${r.departamento_nombre}` : r.departamento_codigo,
            }));
            this.filterOptions.set({ ...this.filterOptions(), ...newOptions });
          });
      },
      centro_costo_codigos: () => {
        this.reportBIService.getFilterCentrosCosto()
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe(res => {
            newOptions['centro_costo_codigos'] = res.map(r => {
              const code = String(r.centro_costo_codigo);
              return {
                value: code,
                label: r.centro_costo_nombre ? `${code} - ${r.centro_costo_nombre}` : code,
              };
            });
            this.filterOptions.set({ ...this.filterOptions(), ...newOptions });
          });
      },
      tipo_doc: () => {
        this.reportBIService.getFilterTiposDoc(source)
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe(res => {
            newOptions['tipo_doc'] = res.map(r => ({ value: r.tipo, label: r.tipo }));
            this.filterOptions.set({ ...this.filterOptions(), ...newOptions });
          });
      },
      actividad_codigos: () => {
        this.reportBIService.getFilterActividades()
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe(res => {
            newOptions['actividad_codigos'] = res.map(r => ({ value: r.actividad_codigo, label: r.actividad_codigo }));
            this.filterOptions.set({ ...this.filterOptions(), ...newOptions });
          });
      },
    };

    for (const f of filters) {
      if (f.type === 'multi_select' && loadMap[f.key]) {
        loadMap[f.key]();
      }
    }
  }

  getOptions(key: string): FilterSelectOption[] {
    return this.filterOptions()[key] ?? [];
  }

  // ── Scalar filters ─────────────────────────────────────────

  getFilterValue(key: string): unknown {
    return this.filters()[key] ?? null;
  }

  updateFilter(key: string, value: unknown): void {
    const updated = { ...this.filters(), [key]: value };
    if (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0)) {
      delete updated[key];
    }
    this.filtersChange.emit(updated);
  }

  clearFilter(key: string): void {
    const updated = { ...this.filters() };
    delete updated[key];
    this.filtersChange.emit(updated);
  }

  clearAll(): void {
    this.filtersChange.emit({});
  }

  // ── Date filters ────────────────────────────────────────────

  getFilterDate(key: string): Date | null {
    const val = this.filters()[key];
    if (!val) return null;
    if (val instanceof Date) return val;
    const [year, month, day] = (val as string).split('-').map(Number);
    return new Date(year, month - 1, day);
  }

  updateFilterDate(key: string, value: Date | null): void {
    if (!value) { this.clearFilter(key); return; }
    const y = value.getFullYear();
    const m = String(value.getMonth() + 1).padStart(2, '0');
    const d = String(value.getDate()).padStart(2, '0');
    this.updateFilter(key, `${y}-${m}-${d}`);
  }

  // ── Array filters (multi_select) ────────────────────────────

  getFilterArray(key: string): string[] {
    const val = this.filters()[key];
    return Array.isArray(val) ? (val as string[]) : [];
  }

  // ── Autocomplete multi (terceros) ───────────────────────────

  onTerceroSearch(q: string): void {
    this.terceroSearch$.next(q);
  }

  addTercero(key: string, option: FilterSelectOption): void {
    const arr = this.getFilterArray(key);
    if (!arr.includes(option.value)) {
      this.filtersChange.emit({ ...this.filters(), [key]: [...arr, option.value] });
    }
  }

  removeTercero(key: string, value: string): void {
    const arr = this.getFilterArray(key).filter(v => v !== value);
    const updated = { ...this.filters(), [key]: arr };
    if (arr.length === 0) delete updated[key];
    this.filtersChange.emit(updated);
  }

  getTerceroLabel(value: string): string {
    const opt = this.terceroOptions().find(o => o.value === value);
    return opt?.label ?? value;
  }

  // ── Misc ────────────────────────────────────────────────────

  get activeFilterCount(): number {
    return Object.keys(this.filters()).length;
  }
}
