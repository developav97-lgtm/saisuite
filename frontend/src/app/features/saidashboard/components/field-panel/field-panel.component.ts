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
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatExpansionModule } from '@angular/material/expansion';
import { BIAggregation, BIFieldConfig, BIFieldDef } from '../../models/bi-field.model';
import { ReportBIService } from '../../services/report-bi.service';

@Component({
  selector: 'app-field-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatCheckboxModule,
    MatIconModule,
    MatSelectModule,
    MatFormFieldModule,
    MatExpansionModule,
  ],
  templateUrl: './field-panel.component.html',
  styleUrl: './field-panel.component.scss',
})
export class FieldPanelComponent {
  private readonly reportBIService = inject(ReportBIService);
  private readonly destroyRef = inject(DestroyRef);

  readonly sources = input<string[]>([]);
  readonly selectedFields = input<BIFieldConfig[]>([]);
  readonly fieldsChange = output<BIFieldConfig[]>();

  /** category -> fields[], grouped by source */
  readonly fieldsByCategory = signal<{ category: string; source: string; fields: BIFieldDef[] }[]>([]);

  readonly aggregations: { value: BIAggregation; label: string }[] = [
    { value: 'SUM', label: 'Suma' },
    { value: 'AVG', label: 'Promedio' },
    { value: 'COUNT', label: 'Conteo' },
    { value: 'MIN', label: 'Mínimo' },
    { value: 'MAX', label: 'Máximo' },
  ];

  constructor() {
    effect(() => {
      const srcs = this.sources();
      if (srcs.length > 0) {
        this.loadFields(srcs);
      } else {
        this.fieldsByCategory.set([]);
      }
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
}
