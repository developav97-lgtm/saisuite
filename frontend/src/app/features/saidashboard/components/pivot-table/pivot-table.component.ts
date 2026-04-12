import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  output,
} from '@angular/core';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ReportBIPivotResult } from '../../models/report-bi.model';
import { BIFieldConfig, BIFieldFormat } from '../../models/bi-field.model';

export interface PivotCellClick {
  rowKey: string;
  colKey: string;
  value: number;
  rowHeaders: Record<string, unknown>;
  colHeaders: Record<string, unknown>;
}

@Component({
  selector: 'app-pivot-table',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatTableModule, MatTooltipModule, MatProgressBarModule],
  templateUrl: './pivot-table.component.html',
  styleUrl: './pivot-table.component.scss',
})
export class PivotTableComponent {
  readonly data = input<ReportBIPivotResult | null>(null);
  readonly loading = input(false);
  readonly fieldConfigs = input<BIFieldConfig[]>([]);
  readonly cellClick = output<PivotCellClick>();

  private readonly formatMap = computed(() => {
    const map = new Map<string, BIFieldFormat>();
    this.fieldConfigs().forEach(fc => {
      if (fc.format) {
        map.set(fc.field, fc.format);
        const agg = (fc.aggregation ?? 'sum').toLowerCase();
        map.set(`${fc.field}_${agg}`, fc.format);
        if (fc.is_calculated) map.set(fc.field, fc.format);
      }
    });
    return map;
  });

  /** True cuando no hay dimensión de columna (pivot sin columnas → una col por métrica). */
  readonly noColumnMode = computed(() => this.data()?.no_column_mode ?? false);

  /** Number of row-axis dimensions */
  readonly rowDimCount = computed(() => {
    const d = this.data();
    if (!d || d.row_headers.length === 0) return 1;
    return Object.keys(d.row_headers[0]).length;
  });

  /** Row dimension field names */
  readonly rowDimFields = computed(() => {
    const d = this.data();
    if (!d || d.row_headers.length === 0) return [];
    return Object.keys(d.row_headers[0]);
  });

  /** Column header display strings (solo modo con-columna) */
  readonly colKeys = computed(() => {
    const d = this.data();
    if (!d || this.noColumnMode()) return [];
    return d.col_headers.map(h => this.headerToKey(h));
  });

  readonly colLabels = computed(() => {
    const d = this.data();
    if (!d || this.noColumnMode()) return [];
    return d.col_headers.map(h => Object.values(h).join(' / '));
  });

  /** Value alias de la primera métrica (modo con-columna, legacy) */
  readonly valueAlias = computed(() => {
    const d = this.data();
    return d?.value_aliases?.[0] ?? '';
  });

  /** Todas las métricas disponibles */
  readonly valueAliases = computed(() => this.data()?.value_aliases ?? []);

  /** Row data */
  readonly rowData = computed(() => {
    const d = this.data();
    if (!d) return [];
    return d.row_headers.map(h => ({
      headers: h,
      key: this.headerToKey(h),
    }));
  });

  readonly hasData = computed(() => {
    const d = this.data();
    return d !== null && d.row_headers.length > 0;
  });

  // ── Etiquetas de métricas ────────────────────────────────────

  getMetricLabel(alias: string): string {
    const d = this.data();
    if (d?.value_labels?.[alias]) return d.value_labels[alias];
    // Fallback: buscar en fieldConfigs
    const fc = this.fieldConfigs().find(f => {
      const agg = (f.aggregation ?? 'SUM').toLowerCase();
      return `${f.field}_${agg}` === alias;
    });
    if (fc) return fc.label;
    return alias;
  }

  // ── Modo sin-columna: valores desde row_totals ───────────────

  getMetricValue(rowKey: string, alias: string): number | null {
    const d = this.data();
    if (!d) return null;
    const totals = d.row_totals[rowKey];
    if (!totals) return null;
    return (totals[alias] as number) ?? null;
  }

  getGrandTotalForAlias(alias: string): number | null {
    const d = this.data();
    if (!d || !d.grand_total) return null;
    return (d.grand_total[alias] as number) ?? null;
  }

  // ── Formato de valores ───────────────────────────────────────

  getMetricFormat(alias: string): BIFieldFormat {
    return this.formatMap().get(alias) ?? 'number';
  }

  formatValue(value: number | null, alias: string): string {
    if (value === null) return '—';
    const fmt = this.getMetricFormat(alias);
    const n = value.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    return fmt === 'currency' ? `$ ${n}` : n;
  }

  // ── Modo con-columna: métodos por alias ──────────────────────

  getCellValueForAlias(rowKey: string, colKey: string, alias: string): number | null {
    const cell = this.data()?.data[`${rowKey}___${colKey}`];
    return cell ? (cell[alias] as number) ?? null : null;
  }

  getRowTotalForAlias(rowKey: string, alias: string): number | null {
    const totals = this.data()?.row_totals[rowKey];
    return totals ? (totals[alias] as number) ?? null : null;
  }

  getColTotalForAlias(colKey: string, alias: string): number | null {
    const totals = this.data()?.col_totals?.[colKey];
    return totals ? (totals[alias] as number) ?? null : null;
  }

  // ── Modo con-columna (original) ──────────────────────────────

  getCellValue(rowKey: string, colKey: string): number | null {
    const d = this.data();
    if (!d) return null;
    const cellKey = `${rowKey}___${colKey}`;
    const cell = d.data[cellKey];
    if (!cell) return null;
    const alias = this.valueAlias();
    return alias ? (cell[alias] as number) ?? null : null;
  }

  getRowTotal(rowKey: string): number | null {
    const d = this.data();
    if (!d) return null;
    const totals = d.row_totals[rowKey];
    if (!totals) return null;
    const alias = this.valueAlias();
    return alias ? (totals[alias] as number) ?? null : null;
  }

  getColTotal(colKey: string): number | null {
    const d = this.data();
    if (!d) return null;
    const totals = d.col_totals[colKey];
    if (!totals) return null;
    const alias = this.valueAlias();
    return alias ? (totals[alias] as number) ?? null : null;
  }

  getGrandTotal(): number | null {
    const d = this.data();
    if (!d || !d.grand_total) return null;
    const alias = this.valueAlias();
    return alias ? (d.grand_total[alias] as number) ?? null : null;
  }

  onCellClick(rowKey: string, colKey: string, value: number | null): void {
    if (value === null) return;
    const d = this.data();
    if (!d) return;
    const rh = d.row_headers.find(h => this.headerToKey(h) === rowKey) ?? {};
    const ch = d.col_headers.find(h => this.headerToKey(h) === colKey) ?? {};
    this.cellClick.emit({ rowKey, colKey, value, rowHeaders: rh, colHeaders: ch });
  }

  headerToKey(h: Record<string, unknown>): string {
    return Object.values(h).map(v => (v != null ? String(v) : '')).join('|');
  }
}
