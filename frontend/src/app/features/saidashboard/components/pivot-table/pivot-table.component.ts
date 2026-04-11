import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  output,
} from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ReportBIPivotResult } from '../../models/report-bi.model';

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
  imports: [DecimalPipe, MatTableModule, MatTooltipModule, MatProgressBarModule],
  templateUrl: './pivot-table.component.html',
  styleUrl: './pivot-table.component.scss',
})
export class PivotTableComponent {
  readonly data = input<ReportBIPivotResult | null>(null);
  readonly loading = input(false);
  readonly cellClick = output<PivotCellClick>();

  /** Number of row-axis dimensions (e.g. 2 if rows=['cuenta','tercero']) */
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

  /** Column header display strings */
  readonly colKeys = computed(() => {
    const d = this.data();
    if (!d) return [];
    return d.col_headers.map(h => this.headerToKey(h));
  });

  /** Column header labels for display */
  readonly colLabels = computed(() => {
    const d = this.data();
    if (!d) return [];
    return d.col_headers.map(h => Object.values(h).join(' / '));
  });

  /** Value alias (first metric) for formatting */
  readonly valueAlias = computed(() => {
    const d = this.data();
    return d?.value_aliases?.[0] ?? '';
  });

  /** All display column IDs for mat-table */
  readonly displayedColumns = computed(() => {
    const dims = this.rowDimFields();
    const cols = this.colKeys();
    return [...dims, ...cols, '__row_total'];
  });

  /** Row data for the table */
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
    return Object.values(h).map(v => String(v)).join('|');
  }
}
