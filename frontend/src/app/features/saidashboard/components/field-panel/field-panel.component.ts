import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  computed,
  inject,
  input,
  output,
  signal,
  effect,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { CdkDragDrop, CdkDrag, CdkDropList, CdkDragPlaceholder, CdkDragHandle, moveItemInArray } from '@angular/cdk/drag-drop';
import { MatDialog } from '@angular/material/dialog';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatMenuModule } from '@angular/material/menu';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import {
  BIAggregation,
  BIFieldConfig,
  BIFieldDef,
  BIFieldFormat,
  BIJoinInfo,
} from '../../models/bi-field.model';
import { ReportBIVisualization } from '../../models/report-bi.model';
import { ReportBIService } from '../../services/report-bi.service';
import { CalcFieldStoreService, CalcFieldTemplate } from '../../services/calc-field-store.service';
import { getSourceLabel } from '../../models/bi-source.model';

/** Campo enriquecido con metadatos de fuente para el panel unificado. */
interface FieldGroupItem extends BIFieldDef {
  source: string;
  sourceLabel: string;
  /** true cuando otro campo con la misma etiqueta existe en otra fuente. */
  showBadge: boolean;
}

/** Grupo de categoría con campos de todas las fuentes fusionados. */
interface MergedGroup {
  category: string;
  fields: FieldGroupItem[];
}
import { CalcFieldDialogComponent, CalcFieldDialogData } from './calc-field-dialog.component';

@Component({
  selector: 'app-field-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    CdkDrag,
    CdkDropList,
    CdkDragPlaceholder,
    CdkDragHandle,
    MatCheckboxModule,
    MatIconModule,
    MatSelectModule,
    MatFormFieldModule,
    MatInputModule,
    MatMenuModule,
    MatButtonModule,
    MatTooltipModule,
    MatChipsModule,
  ],
  templateUrl: './field-panel.component.html',
  styleUrl: './field-panel.component.scss',
})
export class FieldPanelComponent {
  private readonly reportBIService = inject(ReportBIService);
  private readonly calcStore = inject(CalcFieldStoreService);
  private readonly dialog = inject(MatDialog);
  private readonly destroyRef = inject(DestroyRef);

  readonly sources = input<string[]>([]);
  readonly selectedFields = input<BIFieldConfig[]>([]);
  readonly visualization = input<ReportBIVisualization>('table');
  readonly fieldsChange = output<BIFieldConfig[]>();

  readonly isPivot = computed(() => this.visualization() === 'pivot');

  readonly dimensionRoles: { value: 'dimension' | 'column'; label: string }[] = [
    { value: 'dimension', label: 'Fila' },
    { value: 'column',    label: 'Columna' },
  ];

  readonly aggregations: { value: BIAggregation; label: string }[] = [
    { value: 'SUM',   label: 'Suma' },
    { value: 'AVG',   label: 'Promedio' },
    { value: 'COUNT', label: 'Conteo' },
    { value: 'MIN',   label: 'Mínimo' },
    { value: 'MAX',   label: 'Máximo' },
  ];

  readonly formatOptions: { value: BIFieldFormat; label: string }[] = [
    { value: 'string',   label: 'Texto' },
    { value: 'number',   label: 'Número' },
    { value: 'currency', label: 'Moneda ($)' },
    { value: 'date',     label: 'Fecha' },
    { value: 'boolean',  label: 'Sí/No' },
  ];

  readonly fieldsByCategory = signal<MergedGroup[]>([]);

  readonly activeJoins = signal<BIJoinInfo[]>([]);
  private allJoins: BIJoinInfo[] = [];
  private joinsLoaded = false;

  readonly activeCalcFields = computed(() =>
    this.selectedFields().filter(f => f.is_calculated),
  );

  private readonly shortLabels: Record<string, string> = {
    gl: 'GL', facturacion: 'FAC', facturacion_detalle: 'DET',
    cartera: 'CART', inventario: 'INV', terceros_saiopen: 'TER',
    productos: 'PROD', cuentas_contables: 'CC',
  };

  /** selectedFields enriquecido con showBadge para el panel de orden. */
  readonly selectedFieldsDisplay = computed(() => {
    const fields = this.selectedFields();
    const labelCount = new Map<string, number>();
    for (const f of fields) {
      labelCount.set(f.label, (labelCount.get(f.label) ?? 0) + 1);
    }
    return fields.map(f => ({
      ...f,
      showBadge: (labelCount.get(f.label) ?? 0) > 1,
      shortSource: this.shortLabels[f.source] ?? f.source.slice(0, 3).toUpperCase(),
    }));
  });

  readonly savedTemplates = signal<CalcFieldTemplate[]>([]);

  /** Término de búsqueda para filtrar el listado de campos. */
  readonly searchTerm = signal('');

  /** Lista de grupos filtrada por el buscador (busca en label y sourceLabel). */
  readonly filteredFieldsByCategory = computed(() => {
    const q = this.searchTerm().toLowerCase().trim();
    const groups = this.fieldsByCategory();
    if (!q) return groups;
    return groups
      .map(g => ({
        ...g,
        fields: g.fields.filter(f =>
          f.label.toLowerCase().includes(q) ||
          f.sourceLabel.toLowerCase().includes(q),
        ),
      }))
      .filter(g => g.fields.length > 0);
  });

  readonly availableMetrics = computed(() =>
    this.fieldsByCategory()
      .flatMap(g => g.fields)
      .filter(f => f.role === 'metric'),
  );

  private lastSourceKey = '';

  constructor() {
    effect(() => {
      const srcs = this.sources();
      const key = [...srcs].sort().join(',');
      if (srcs.length === 0) {
        this.fieldsByCategory.set([]);
        this.activeJoins.set([]);
        this.searchTerm.set('');
        this.lastSourceKey = '';
      } else if (key !== this.lastSourceKey) {
        this.lastSourceKey = key;
        this.searchTerm.set('');
        this.loadFields(srcs);
        this.updateActiveJoins(srcs);
      }
    });

    effect(() => {
      const srcs = this.sources();
      if (srcs.length === 0) { this.savedTemplates.set([]); return; }
      const templates: CalcFieldTemplate[] = [];
      for (const src of srcs) {
        templates.push(...this.calcStore.getTemplates(src));
      }
      this.savedTemplates.set(templates);
    });
  }

  private updateActiveJoins(srcs: string[]): void {
    if (srcs.length < 2) { this.activeJoins.set([]); return; }
    if (!this.joinsLoaded) {
      this.reportBIService.getJoins()
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: joins => {
            this.allJoins = joins;
            this.joinsLoaded = true;
            this.activeJoins.set(this.filterJoinsForSources(srcs));
          },
          error: () => {},
        });
    } else {
      this.activeJoins.set(this.filterJoinsForSources(srcs));
    }
  }

  private filterJoinsForSources(srcs: string[]): BIJoinInfo[] {
    if (srcs.length < 2) return [];
    return this.allJoins.filter(j =>
      srcs.includes(j.source_a) && srcs.includes(j.source_b),
    );
  }

  getJoinDescription(join: BIJoinInfo): string {
    const a = getSourceLabel(join.source_a);
    const b = getSourceLabel(join.source_b);
    return join.description || `${a} ↔ ${b}`;
  }

  private loadFields(srcs: string[]): void {
    const raw: { category: string; source: string; fields: BIFieldDef[] }[] = [];
    let pending = srcs.length;

    for (const src of srcs) {
      this.reportBIService.getFields(src)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: data => {
            for (const [category, fields] of Object.entries(data)) {
              raw.push({ category, source: src, fields: fields as BIFieldDef[] });
            }
            pending--;
            if (pending === 0) this.fieldsByCategory.set(this.mergeCategories(raw));
          },
          error: () => { pending--; },
        });
    }
  }

  /** Fusiona grupos de igual categoría y calcula si cada campo necesita badge de fuente. */
  private mergeCategories(
    raw: { category: string; source: string; fields: BIFieldDef[] }[],
  ): MergedGroup[] {
    // 1. Detectar etiquetas duplicadas entre fuentes
    const labelToSources = new Map<string, Set<string>>();
    for (const g of raw) {
      for (const f of g.fields) {
        if (!labelToSources.has(f.label)) labelToSources.set(f.label, new Set());
        labelToSources.get(f.label)!.add(g.source);
      }
    }

    // 2. Orden de categorías (primer aparición)
    const catOrder: string[] = [];
    const seen = new Set<string>();
    for (const g of raw) {
      if (!seen.has(g.category)) { catOrder.push(g.category); seen.add(g.category); }
    }

    // 3. Fusionar campos por categoría
    const merged = new Map<string, FieldGroupItem[]>();
    for (const cat of catOrder) merged.set(cat, []);

    for (const g of raw) {
      const items: FieldGroupItem[] = g.fields.map(f => ({
        ...f,
        source: g.source,
        sourceLabel: getSourceLabel(g.source),
        showBadge: (labelToSources.get(f.label)?.size ?? 0) > 1,
      }));
      merged.get(g.category)!.push(...items);
    }

    return catOrder.map(cat => ({ category: cat, fields: merged.get(cat)! }));
  }

  defaultFormat(fieldDef: BIFieldDef): BIFieldFormat {
    if (fieldDef.role === 'metric') return 'number';
    if (fieldDef.type === 'date') return 'date';
    if (fieldDef.type === 'boolean') return 'boolean';
    return 'string';
  }

  isFieldSelected(source: string, field: string): boolean {
    return this.selectedFields().some(f => f.source === source && f.field === field);
  }

  getFieldConfig(source: string, field: string): BIFieldConfig | undefined {
    return this.selectedFields().find(f => f.source === source && f.field === field);
  }

  toggleField(source: string, fieldDef: BIFieldDef): void {
    const current = this.selectedFields();
    if (this.isFieldSelected(source, fieldDef.field)) {
      this.fieldsChange.emit(current.filter(f => !(f.source === source && f.field === fieldDef.field)));
    } else {
      const config: BIFieldConfig = {
        source,
        field: fieldDef.field,
        role: fieldDef.role,
        label: fieldDef.label,
        format: this.defaultFormat(fieldDef),
        ...(fieldDef.role === 'metric' ? { aggregation: 'SUM' as BIAggregation } : {}),
      };
      this.fieldsChange.emit([...current, config]);
    }
  }

  onAggregationChange(source: string, field: string, agg: BIAggregation): void {
    this.fieldsChange.emit(
      this.selectedFields().map(f =>
        f.source === source && f.field === field ? { ...f, aggregation: agg } : f,
      ),
    );
  }

  onRoleChange(source: string, field: string, role: 'dimension' | 'column'): void {
    this.fieldsChange.emit(
      this.selectedFields().map(f =>
        f.source === source && f.field === field ? { ...f, role } : f,
      ),
    );
  }

  onFormatChange(source: string, field: string, format: BIFieldFormat): void {
    this.fieldsChange.emit(
      this.selectedFields().map(f =>
        f.source === source && f.field === field ? { ...f, format } : f,
      ),
    );
  }

  formatIcon(format: BIFieldFormat | undefined): string {
    switch (format) {
      case 'currency': return '$';
      case 'number':   return '#';
      case 'date':     return 'D';
      case 'boolean':  return 'S';
      default:         return 'T';
    }
  }

  onFieldReorder(event: CdkDragDrop<BIFieldConfig[]>): void {
    const fields = [...this.selectedFields()];
    moveItemInArray(fields, event.previousIndex, event.currentIndex);
    this.fieldsChange.emit(fields);
  }

  removeField(source: string, field: string): void {
    this.fieldsChange.emit(
      this.selectedFields().filter(f => !(f.source === source && f.field === field)),
    );
  }

  removeCalcField(fieldId: string): void {
    this.fieldsChange.emit(this.selectedFields().filter(f => f.field !== fieldId));
  }

  // ── Búsqueda ────────────────────────────────────────────────────

  onSearchInput(event: Event): void {
    this.searchTerm.set((event.target as HTMLInputElement).value);
  }

  clearSearch(): void {
    this.searchTerm.set('');
  }

  // ── Modal campo calculado ────────────────────────────────────────

  openCalcDialog(): void {
    const ref = this.dialog.open(CalcFieldDialogComponent, {
      data: {
        sources: this.sources(),
        metrics: this.availableMetrics(),
        templates: [...this.savedTemplates()],
      } satisfies CalcFieldDialogData,
      width: '480px',
      maxWidth: '95vw',
    });

    ref.afterClosed()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((result: BIFieldConfig | null) => {
        if (result) {
          this.fieldsChange.emit([...this.selectedFields(), result]);
        }
        // Recargar plantillas (puede haber creado o eliminado una en el dialog)
        const templates: CalcFieldTemplate[] = [];
        for (const src of this.sources()) {
          templates.push(...this.calcStore.getTemplates(src));
        }
        this.savedTemplates.set(templates);
      });
  }
}
