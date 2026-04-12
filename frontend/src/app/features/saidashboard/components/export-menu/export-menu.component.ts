import {
  ChangeDetectionStrategy,
  Component,
  inject,
  input,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { utils, writeFileXLSX } from 'xlsx';

import { saveAs } from 'file-saver';
import {
  ReportBIExecuteResult,
  ReportBIPivotResult,
  isTableResult,
  isPivotResult,
} from '../../models/report-bi.model';
import { BIFieldConfig } from '../../models/bi-field.model';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-export-menu',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatButtonModule, MatIconModule, MatMenuModule],
  template: `
    <button mat-stroked-button [matMenuTriggerFor]="exportMenu" [disabled]="!data()">
      <mat-icon>download</mat-icon>
      Exportar
    </button>
    <mat-menu #exportMenu="matMenu">
      <button mat-menu-item (click)="exportExcel()">
        <mat-icon>table_chart</mat-icon>
        Excel (.xlsx)
      </button>
      <button mat-menu-item (click)="exportCsv()">
        <mat-icon>description</mat-icon>
        CSV (.csv)
      </button>
    </mat-menu>
  `,
})
export class ExportMenuComponent {
  private readonly toast = inject(ToastService);

  readonly data = input<ReportBIExecuteResult | null>(null);
  readonly title = input('Reporte');
  readonly reportId = input<string | null>(null);
  readonly fieldConfigs = input<BIFieldConfig[]>([]);

  exportExcel(): void {
    const d = this.data();
    if (!d) return;

    const wb = utils.book_new();

    if (isTableResult(d)) {
      // Construir mapa de formato por campo
      const formatMap = new Map<string, string>();
      for (const fc of this.fieldConfigs()) {
        if (fc.format === 'currency' || fc.format === 'number') {
          formatMap.set(fc.field, '#,##0.00');
        } else if (fc.format === 'date') {
          formatMap.set(fc.field, 'DD/MM/YYYY');
        }
      }

      // Construir filas con tipos correctos
      const headers = d.columns.map(c => c.label);
      const dataRows = d.rows.map(row =>
        d.columns.map(col => {
          const val = row[col.field];
          const fmt = formatMap.get(col.field);
          // Si tiene formato numérico, convertir a número para que Excel pueda sumar
          if (fmt && fmt.includes('#') && val !== null && val !== undefined) {
            const num = Number(val);
            return isNaN(num) ? String(val ?? '') : num;
          }
          return String(val ?? '');
        }),
      );

      const ws = utils.aoa_to_sheet([headers, ...dataRows]);

      // Aplicar numFmt a celdas numéricas
      d.columns.forEach((col, ci) => {
        const fmt = formatMap.get(col.field);
        if (!fmt) return;
        for (let ri = 1; ri <= dataRows.length; ri++) {
          const cellRef = utils.encode_cell({ r: ri, c: ci });
          const cell = ws[cellRef] as Record<string, unknown> | undefined;
          if (cell && (cell['t'] === 'n' || typeof cell['v'] === 'number')) {
            cell['z'] = fmt;
          }
        }
      });

      utils.book_append_sheet(wb, ws, 'Datos');
    } else if (isPivotResult(d)) {
      const ws = this.pivotToSheet(d);
      utils.book_append_sheet(wb, ws, 'Pivot');
    }

    writeFileXLSX(wb, `${this.sanitizeFilename(this.title())}.xlsx`);
    this.toast.success('Archivo Excel descargado.');
  }

  exportCsv(): void {
    const d = this.data();
    if (!d || !isTableResult(d)) {
      this.toast.error('Solo se puede exportar CSV en vista de tabla.');
      return;
    }

    const header = d.columns.map(c => c.label).join(',');
    const rows = d.rows.map(row =>
      d.columns.map(col => {
        const val = row[col.field];
        if (val === null || val === undefined) return '';
        const str = String(val);
        return str.includes(',') || str.includes('"') ? `"${str.replace(/"/g, '""')}"` : str;
      }).join(','),
    );

    const csv = [header, ...rows].join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    saveAs(blob, `${this.sanitizeFilename(this.title())}.csv`);
    this.toast.success('Archivo CSV descargado.');
  }

  private pivotToSheet(d: ReportBIPivotResult) {
    const rows: Record<string, unknown>[] = [];
    const rowDims = d.row_headers.length > 0 ? Object.keys(d.row_headers[0]) : [];
    const colLabels = d.col_headers.map(h => Object.values(h).join(' / '));
    const alias = d.value_aliases[0] ?? '';

    for (const rh of d.row_headers) {
      const rk = Object.values(rh).map(v => String(v)).join('|');
      const row: Record<string, unknown> = { ...rh };
      for (let ci = 0; ci < d.col_headers.length; ci++) {
        const ck = Object.values(d.col_headers[ci]).map(v => String(v)).join('|');
        const cell = d.data[`${rk}___${ck}`];
        row[colLabels[ci]] = cell?.[alias] ?? null;
      }
      const rt = d.row_totals[rk];
      row['Total'] = rt?.[alias] ?? null;
      rows.push(row);
    }

    // Fila de totales
    const totalRow: Record<string, unknown> = {};
    rowDims.forEach((dim, i) => { totalRow[dim] = i === 0 ? 'Total' : ''; });
    for (let ci = 0; ci < d.col_headers.length; ci++) {
      const ck = Object.values(d.col_headers[ci]).map(v => String(v)).join('|');
      const ct = d.col_totals[ck];
      totalRow[colLabels[ci]] = ct?.[alias] ?? null;
    }
    totalRow['Total'] = d.grand_total?.[alias] ?? null;
    rows.push(totalRow);

    return utils.json_to_sheet(rows);
  }

  private sanitizeFilename(name: string): string {
    return name.replace(/[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ _-]/g, '').substring(0, 100) || 'reporte';
  }
}
