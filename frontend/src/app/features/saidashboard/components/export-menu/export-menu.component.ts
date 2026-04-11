import {
  ChangeDetectionStrategy,
  Component,
  inject,
  input,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { utils, writeFileXLSX } from 'xlsx';
import { saveAs } from 'file-saver';
import {
  ReportBIExecuteResult,
  ReportBIPivotResult,
  isTableResult,
  isPivotResult,
} from '../../models/report-bi.model';
import { ReportBIService } from '../../services/report-bi.service';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-export-menu',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatButtonModule, MatIconModule, MatMenuModule, MatProgressSpinnerModule],
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
      <button mat-menu-item (click)="exportPdf()">
        <mat-icon>picture_as_pdf</mat-icon>
        PDF
      </button>
    </mat-menu>
  `,
})
export class ExportMenuComponent {
  private readonly reportService = inject(ReportBIService);
  private readonly toast = inject(ToastService);

  readonly data = input<ReportBIExecuteResult | null>(null);
  readonly title = input('Reporte');
  readonly reportId = input<string | null>(null);

  exportExcel(): void {
    const d = this.data();
    if (!d) return;

    const wb = utils.book_new();

    if (isTableResult(d)) {
      const ws = utils.json_to_sheet(d.rows, { header: d.columns });
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

    const header = d.columns.join(',');
    const rows = d.rows.map(row =>
      d.columns.map(col => {
        const val = row[col];
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

  exportPdf(): void {
    const id = this.reportId();
    if (!id) {
      this.toast.error('Guarda el reporte antes de exportar a PDF.');
      return;
    }

    this.reportService.exportPdf(id).subscribe({
      next: (blob) => {
        saveAs(blob, `${this.sanitizeFilename(this.title())}.pdf`);
        this.toast.success('PDF descargado.');
      },
      error: () => this.toast.error('Error al generar el PDF.'),
    });
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

    // Totals row
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
