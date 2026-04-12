import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnDestroy,
  computed,
  effect,
  input,
  output,
  ViewChild,
} from '@angular/core';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginatorModule, MatPaginator } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { DecimalPipe, DatePipe } from '@angular/common';
import { ReportBITableResult } from '../../models/report-bi.model';
import { BIFieldConfig, BIFieldFormat } from '../../models/bi-field.model';

@Component({
  selector: 'app-data-table',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatTableModule,
    MatPaginatorModule,
    MatProgressBarModule,
    DecimalPipe,
    DatePipe,
  ],
  templateUrl: './data-table.component.html',
  styleUrl: './data-table.component.scss',
})
export class DataTableComponent implements AfterViewInit, OnDestroy {
  readonly data = input<ReportBITableResult | null>(null);
  readonly loading = input(false);
  readonly fieldConfigs = input<BIFieldConfig[]>([]);
  readonly cellClick = output<{ row: Record<string, unknown>; column: string }>();

  // Setter: connects paginator whenever it enters the DOM (it's inside @if).
  @ViewChild(MatPaginator) set paginator(p: MatPaginator) {
    this.dataSource.paginator = p ?? null;
  }

  @ViewChild('topTrack')  topTrack!:  ElementRef<HTMLDivElement>;
  @ViewChild('topSpacer') topSpacer!: ElementRef<HTMLDivElement>;
  @ViewChild('tableWrap') tableWrap!: ElementRef<HTMLDivElement>;

  readonly dataSource = new MatTableDataSource<Record<string, unknown>>([]);

  /** Field names used as matColumnDef keys. */
  readonly columnFields = computed(() => this.data()?.columns.map(c => c.field) ?? []);

  /** label map: field → display label */
  readonly columnLabels = computed(() => {
    const map = new Map<string, string>();
    this.data()?.columns.forEach(c => map.set(c.field, c.label));
    return map;
  });

  /** Mapa: field → formato configurado por el usuario.
   *  Mapea tanto 'debito' como 'debito_sum' (sufijo que agrega el backend para métricas). */
  private readonly formatMap = computed(() => {
    const map = new Map<string, BIFieldFormat>();
    this.fieldConfigs().forEach(fc => {
      if (fc.format) {
        map.set(fc.field, fc.format);
        const agg = (fc.aggregation ?? 'sum').toLowerCase();
        map.set(`${fc.field}_${agg}`, fc.format);
      }
    });
    return map;
  });

  /** Mapa: field → tipo de columna (dimension|metric) desde el resultado */
  private readonly columnTypeMap = computed(() => {
    const map = new Map<string, 'dimension' | 'metric'>();
    this.data()?.columns.forEach(c => map.set(c.field, c.type));
    return map;
  });

  readonly hasData = computed(() => {
    const d = this.data();
    return d !== null && d.rows.length > 0;
  });

  private resizeObserver?: ResizeObserver;
  private syncingScroll = false;

  constructor() {
    effect(() => {
      this.dataSource.data = this.data()?.rows ?? [];
    });
  }

  ngAfterViewInit(): void {
    if (!this.tableWrap) return;
    this.resizeObserver = new ResizeObserver(() => {
      if (this.topSpacer) {
        this.topSpacer.nativeElement.style.minWidth =
          `${this.tableWrap.nativeElement.scrollWidth}px`;
      }
    });
    this.resizeObserver.observe(this.tableWrap.nativeElement);
  }

  ngOnDestroy(): void {
    this.resizeObserver?.disconnect();
  }

  onTopScroll(): void {
    if (this.syncingScroll || !this.tableWrap) return;
    this.syncingScroll = true;
    this.tableWrap.nativeElement.scrollLeft = this.topTrack.nativeElement.scrollLeft;
    this.syncingScroll = false;
  }

  onTableScroll(): void {
    if (this.syncingScroll || !this.topTrack) return;
    this.syncingScroll = true;
    this.topTrack.nativeElement.scrollLeft = this.tableWrap.nativeElement.scrollLeft;
    this.syncingScroll = false;
  }

  getLabel(field: string): string {
    return this.columnLabels().get(field) ?? field;
  }

  /** Retorna el formato a aplicar para un campo: usa config del usuario, con fallback por tipo de columna. */
  getFormat(field: string): BIFieldFormat {
    const userFmt = this.formatMap().get(field);
    if (userFmt) return userFmt;
    const colType = this.columnTypeMap().get(field);
    return colType === 'metric' ? 'number' : 'string';
  }

  isNumericFormat(field: string): boolean {
    const fmt = this.getFormat(field);
    return fmt === 'number' || fmt === 'currency';
  }

  onCellClick(row: Record<string, unknown>, column: string): void {
    this.cellClick.emit({ row, column });
  }
}
