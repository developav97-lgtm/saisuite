import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  computed,
  effect,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { provideNativeDateAdapter } from '@angular/material/core';
import {
  BIFieldDef,
  BIFieldOption,
  BIFieldType,
  BIFilterOperator,
  BIFilterV2,
  OPERATORS_BY_TYPE,
} from '../../models/bi-field.model';
import { ReportBIService } from '../../services/report-bi.service';
import { getSourceLabel } from '../../models/bi-source.model';

interface PendingFilter {
  source: string;
  field: string;
  fieldLabel: string;
  fieldType: BIFieldType;
  operator: BIFilterOperator;
  valueScalar: string;
  valueFrom: string;
  valueTo: string;
  valueList: string;
}

const DEFAULT_PENDING: PendingFilter = {
  source: '',
  field: '',
  fieldLabel: '',
  fieldType: 'text',
  operator: 'eq',
  valueScalar: '',
  valueFrom: '',
  valueTo: '',
  valueList: '',
};

@Component({
  selector: 'app-filter-builder',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [provideNativeDateAdapter()],
  imports: [
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatAutocompleteModule,
    MatDatepickerModule,
    MatSelectModule,
    MatIconModule,
    MatButtonModule,
    MatChipsModule,
    MatTooltipModule,
  ],
  templateUrl: './filter-builder.component.html',
  styleUrl: './filter-builder.component.scss',
})
export class FilterBuilderComponent {
  private readonly reportBIService = inject(ReportBIService);
  private readonly destroyRef = inject(DestroyRef);

  // ViewChild con signal API (Angular 17+)
  private readonly fieldInputEl = viewChild<ElementRef<HTMLInputElement>>('fieldInput');

  readonly sources = input<string[]>([]);
  readonly filters = input<BIFilterV2[]>([]);
  readonly layout = input<'sidebar' | 'horizontal'>('sidebar');
  readonly filtersChange = output<BIFilterV2[]>();

  readonly fieldOptions = signal<BIFieldOption[]>([]);
  readonly pending = signal<PendingFilter>({ ...DEFAULT_PENDING });
  readonly addPanelOpen = signal(false);

  // ── Búsqueda en el selector de campo ────────────────────────────
  readonly fieldSearchText = signal('');

  readonly filteredFieldOptions = computed(() => {
    const q = this.fieldSearchText().toLowerCase().trim();
    if (!q) return this.fieldOptions();
    return this.fieldOptions().filter(o =>
      o.label.toLowerCase().includes(q) ||
      o.sourceLabel.toLowerCase().includes(q),
    );
  });

  /** Función displayWith para mat-autocomplete. */
  readonly fieldDisplayFn = (opt: BIFieldOption | null): string => {
    if (!opt) return '';
    return `${opt.sourceLabel} › ${opt.label}`;
  };

  // ── Computed de estado del filtro pendiente ──────────────────────

  readonly availableOperators = computed(() => {
    const type = this.pending().fieldType;
    return OPERATORS_BY_TYPE[type] ?? OPERATORS_BY_TYPE['text'];
  });

  readonly isRangeOp = computed(() => this.pending().operator === 'between');
  readonly isListOp  = computed(() => this.pending().operator === 'in');
  readonly isBoolOp  = computed(() =>
    this.pending().operator === 'is_true' || this.pending().operator === 'is_false',
  );
  readonly isDateField = computed(() => this.pending().fieldType === 'date');

  readonly canAddFilter = computed(() => {
    const p = this.pending();
    if (!p.source || !p.field) return false;
    if (this.isBoolOp()) return true;
    if (this.isRangeOp()) return p.valueFrom.trim().length > 0 && p.valueTo.trim().length > 0;
    if (this.isListOp()) return p.valueList.trim().length > 0;
    return p.valueScalar.trim().length > 0;
  });

  private lastSourceKey = '';

  constructor() {
    effect(() => {
      const srcs = this.sources();
      const key = [...srcs].sort().join(',');
      if (srcs.length === 0) {
        this.fieldOptions.set([]);
        this.lastSourceKey = '';
        return;
      }
      if (key !== this.lastSourceKey) {
        this.lastSourceKey = key;
        this.loadFieldOptions(srcs);
        // Limpiar el input de búsqueda al cambiar fuentes
        const el = this.fieldInputEl()?.nativeElement;
        if (el) el.value = '';
        this.fieldSearchText.set('');
      }
    });
  }

  private loadFieldOptions(srcs: string[]): void {
    const all: BIFieldOption[] = [];
    let pending = srcs.length;

    for (const src of srcs) {
      this.reportBIService.getFields(src)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: data => {
            const sourceLabel = getSourceLabel(src);
            for (const fields of Object.values(data)) {
              for (const f of fields as BIFieldDef[]) {
                all.push({ source: src, sourceLabel, field: f.field, label: f.label, type: f.type, role: f.role });
              }
            }
            pending--;
            if (pending === 0) this.fieldOptions.set(all);
          },
          error: () => { pending--; },
        });
    }
  }

  // ── Autocomplete de campo ────────────────────────────────────────

  onFieldFocus(): void {
    // Al enfocar, mostrar todas las opciones
    this.fieldSearchText.set('');
  }

  onFieldInput(event: Event): void {
    const val = (event.target as HTMLInputElement).value;
    this.fieldSearchText.set(val);
    // Si el usuario borra el campo, resetear selección
    if (!val.trim()) {
      this.pending.update(() => ({ ...DEFAULT_PENDING }));
    }
  }

  onFieldOptionSelected(opt: BIFieldOption): void {
    this.selectField(opt);
    this.fieldSearchText.set('');
  }

  // ── Construcción del filtro pendiente ────────────────────────────

  selectField(option: BIFieldOption): void {
    const defaultOp = OPERATORS_BY_TYPE[option.type]?.[0]?.value ?? 'eq';
    this.pending.update(p => ({
      ...p,
      source: option.source,
      field: option.field,
      fieldLabel: option.label,
      fieldType: option.type,
      operator: defaultOp,
      valueScalar: '',
      valueFrom: '',
      valueTo: '',
      valueList: '',
    }));
  }

  selectOperator(op: BIFilterOperator): void {
    this.pending.update(p => ({
      ...p,
      operator: op,
      valueScalar: '',
      valueFrom: '',
      valueTo: '',
      valueList: '',
    }));
  }

  addFilter(): void {
    if (!this.canAddFilter()) return;

    const p = this.pending();
    let value: unknown;

    if (this.isBoolOp()) {
      value = null;
    } else if (this.isRangeOp()) {
      value = [p.valueFrom.trim(), p.valueTo.trim()];
    } else if (this.isListOp()) {
      value = p.valueList.split(',').map(v => v.trim()).filter(v => v.length > 0);
    } else {
      value = p.valueScalar.trim();
    }

    const newFilter: BIFilterV2 = {
      source: p.source,
      field: p.field,
      operator: p.operator,
      value,
    };

    this.filtersChange.emit([...this.filters(), newFilter]);
    this.pending.set({ ...DEFAULT_PENDING });
    this.addPanelOpen.set(false);
    // Limpiar input del autocomplete
    const el = this.fieldInputEl()?.nativeElement;
    if (el) el.value = '';
  }

  removeFilter(index: number): void {
    this.filtersChange.emit(this.filters().filter((_, i) => i !== index));
  }

  clearAll(): void {
    this.filtersChange.emit([]);
  }

  toggleAddPanel(): void {
    this.addPanelOpen.update(v => !v);
    if (!this.addPanelOpen()) {
      this.pending.set({ ...DEFAULT_PENDING });
      const el = this.fieldInputEl()?.nativeElement;
      if (el) el.value = '';
    }
  }

  // ── Helpers de display ──────────────────────────────────────────

  getFilterSummary(filter: BIFilterV2): string {
    const opt = this.fieldOptions().find(o => o.source === filter.source && o.field === filter.field);
    const fieldLabel = opt?.label ?? filter.field;
    const opLabel = this.getOperatorLabel(filter.operator, opt?.type ?? 'text');

    let valueStr = '';
    if (filter.operator === 'is_true') valueStr = 'sí';
    else if (filter.operator === 'is_false') valueStr = 'no';
    else if (Array.isArray(filter.value)) {
      valueStr = filter.operator === 'in'
        ? (filter.value as (string | number)[]).join(', ')
        : (filter.value as string[]).join(' — ');
    } else {
      valueStr = String(filter.value ?? '');
    }

    return `${fieldLabel} ${opLabel} ${valueStr}`.trim();
  }

  private getOperatorLabel(op: BIFilterOperator, type: BIFieldType): string {
    const ops = OPERATORS_BY_TYPE[type] ?? OPERATORS_BY_TYPE['text'];
    return ops.find(o => o.value === op)?.label ?? op;
  }

  get activeFilterCount(): number {
    return this.filters().length;
  }

  // ── Input handlers (strict-mode) ────────────────────────────────

  onValueScalarInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.pending.update(p => ({ ...p, valueScalar: value }));
  }

  onValueFromInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.pending.update(p => ({ ...p, valueFrom: value }));
  }

  onValueToInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.pending.update(p => ({ ...p, valueTo: value }));
  }

  onValueListInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.pending.update(p => ({ ...p, valueList: value }));
  }

  // ── Date helpers ────────────────────────────────────────────────

  getDateValue(raw: string): Date | null {
    if (!raw) return null;
    const [y, m, d] = raw.split('-').map(Number);
    return new Date(y, m - 1, d);
  }

  setDateScalar(value: Date | null): void {
    if (!value) { this.pending.update(p => ({ ...p, valueScalar: '' })); return; }
    this.pending.update(p => ({ ...p, valueScalar: this.toDateStr(value) }));
  }

  setDateFrom(value: Date | null): void {
    if (!value) { this.pending.update(p => ({ ...p, valueFrom: '' })); return; }
    this.pending.update(p => ({ ...p, valueFrom: this.toDateStr(value) }));
  }

  setDateTo(value: Date | null): void {
    if (!value) { this.pending.update(p => ({ ...p, valueTo: '' })); return; }
    this.pending.update(p => ({ ...p, valueTo: this.toDateStr(value) }));
  }

  private toDateStr(d: Date): string {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
}
