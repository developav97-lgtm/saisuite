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
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatMenuModule } from '@angular/material/menu';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import {
  BIAggregation,
  BIFieldConfig,
  BIFieldDef,
  BIFieldFormat,
} from '../../models/bi-field.model';
import { ReportBIVisualization } from '../../models/report-bi.model';
import { ReportBIService } from '../../services/report-bi.service';
import { CalcFieldStoreService, CalcFieldTemplate } from '../../services/calc-field-store.service';

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
    MatExpansionModule,
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
  ];

  readonly fieldsByCategory = signal<{ category: string; source: string; fields: BIFieldDef[] }[]>([]);

  /** Campos calculados activos en el reporte actual. */
  readonly activeCalcFields = computed(() =>
    this.selectedFields().filter(f => f.is_calculated),
  );

  /** Plantillas guardadas en localStorage para las fuentes actuales. */
  readonly savedTemplates = signal<CalcFieldTemplate[]>([]);

  // ── Formulario para nuevo campo calculado ────────────────────
  calcLabel = '';
  calcFormula = '';
  calcFormat: BIFieldFormat = 'number';

  /** Campos métricos disponibles para usar en fórmulas calculadas. */
  readonly availableMetrics = computed(() =>
    this.fieldsByCategory()
      .flatMap(g => g.fields)
      .filter(f => f.role === 'metric'),
  );

  insertFieldInFormula(fieldName: string): void {
    const sep = this.calcFormula.trim().length > 0 ? ' ' : '';
    this.calcFormula = this.calcFormula + sep + fieldName;
  }

  private lastSourceKey = '';

  constructor() {
    // Efecto: cargar campos del backend cuando cambian las fuentes
    effect(() => {
      const srcs = this.sources();
      const key = [...srcs].sort().join(',');
      if (srcs.length === 0) {
        this.fieldsByCategory.set([]);
        this.lastSourceKey = '';
      } else if (key !== this.lastSourceKey) {
        this.lastSourceKey = key;
        this.loadFields(srcs);
      }
    });

    // Efecto: cargar plantillas guardadas cuando cambian las fuentes
    effect(() => {
      const srcs = this.sources();
      if (srcs.length === 0) {
        this.savedTemplates.set([]);
        return;
      }
      const templates: CalcFieldTemplate[] = [];
      for (const src of srcs) {
        templates.push(...this.calcStore.getTemplates(src));
      }
      this.savedTemplates.set(templates);
    });
  }

  private loadFields(srcs: string[]): void {
    const allCategories: { category: string; source: string; fields: BIFieldDef[] }[] = [];
    let pending = srcs.length;

    for (const src of srcs) {
      this.reportBIService.getFields(src)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: data => {
            for (const [category, fields] of Object.entries(data)) {
              allCategories.push({ category: `${category}`, source: src, fields });
            }
            pending--;
            if (pending === 0) {
              this.fieldsByCategory.set(allCategories);
            }
          },
          error: () => {
            pending--;
          },
        });
    }
  }

  /** Formato por defecto según rol y tipo del campo. */
  defaultFormat(fieldDef: BIFieldDef): BIFieldFormat {
    if (fieldDef.role === 'metric') return 'number';
    if (fieldDef.type === 'date') return 'date';
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
      default:         return 'T';
    }
  }

  onFieldReorder(event: CdkDragDrop<BIFieldConfig[]>): void {
    const fields = [...this.selectedFields()];
    moveItemInArray(fields, event.previousIndex, event.currentIndex);
    this.fieldsChange.emit(fields);
  }

  // ── Campos calculados ─────────────────────────────────────────

  /** Elimina un campo calculado activo del reporte. */
  removeCalcField(fieldId: string): void {
    this.fieldsChange.emit(
      this.selectedFields().filter(f => f.field !== fieldId),
    );
  }

  /** Agrega un campo calculado al reporte desde una plantilla guardada. */
  addTemplateToReport(template: CalcFieldTemplate): void {
    const source = this.sources()[0] ?? '';
    const config: BIFieldConfig = {
      source,
      field: `__calc_${Date.now()}`,
      role: 'metric',
      label: template.label,
      format: template.format,
      is_calculated: true,
      formula: template.formula,
    };
    this.fieldsChange.emit([...this.selectedFields(), config]);
  }

  /** Elimina una plantilla guardada del localStorage. */
  deleteTemplate(template: CalcFieldTemplate): void {
    const source = this.sources()[0] ?? '';
    this.calcStore.removeTemplate(source, template.id);
    this.savedTemplates.update(ts => ts.filter(t => t.id !== template.id));
  }

  /** Agrega nuevo campo calculado al reporte y guarda la plantilla en localStorage. */
  addCalculatedField(): void {
    if (!this.calcLabel.trim() || !this.calcFormula.trim()) return;
    const source = this.sources()[0] ?? '';
    const templateId = `tpl_${Date.now()}`;

    // Guardar plantilla para reutilización futura
    const template: CalcFieldTemplate = {
      id: templateId,
      label: this.calcLabel.trim(),
      formula: this.calcFormula.trim(),
      format: this.calcFormat,
    };
    this.calcStore.saveTemplate(source, template);
    this.savedTemplates.update(ts => [...ts, template]);

    // Agregar al reporte actual
    const config: BIFieldConfig = {
      source,
      field: `__calc_${templateId}`,
      role: 'metric',
      label: this.calcLabel.trim(),
      format: this.calcFormat,
      is_calculated: true,
      formula: this.calcFormula.trim(),
    };
    this.fieldsChange.emit([...this.selectedFields(), config]);
    this.calcLabel = '';
    this.calcFormula = '';
    this.calcFormat = 'number';
  }
}
