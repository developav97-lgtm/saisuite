import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  output,
  signal,
  ViewChild,
  AfterViewInit,
} from '@angular/core';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginatorModule, MatPaginator } from '@angular/material/paginator';
import { MatSortModule, MatSort } from '@angular/material/sort';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { DecimalPipe } from '@angular/common';
import { ReportBITableResult } from '../../models/report-bi.model';

@Component({
  selector: 'app-data-table',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatProgressBarModule,
    DecimalPipe,
  ],
  templateUrl: './data-table.component.html',
  styleUrl: './data-table.component.scss',
})
export class DataTableComponent implements AfterViewInit {
  readonly data = input<ReportBITableResult | null>(null);
  readonly loading = input(false);
  readonly cellClick = output<{ row: Record<string, unknown>; column: string }>();

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  readonly dataSource = new MatTableDataSource<Record<string, unknown>>([]);

  readonly columns = computed(() => this.data()?.columns ?? []);
  readonly totalRows = computed(() => this.data()?.total_count ?? 0);

  readonly hasData = computed(() => {
    const d = this.data();
    return d !== null && d.rows.length > 0;
  });

  ngAfterViewInit(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  ngOnChanges(): void {
    const d = this.data();
    this.dataSource.data = d?.rows ?? [];
  }

  isNumeric(value: unknown): boolean {
    return typeof value === 'number' || (typeof value === 'string' && !isNaN(Number(value)) && value.trim() !== '');
  }

  onCellClick(row: Record<string, unknown>, column: string): void {
    this.cellClick.emit({ row, column });
  }
}
