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
  readonly showPaginator = input(true);
  readonly cellClick = output<{ row: Record<string, unknown>; column: string }>();

  // Setter: connects paginator whenever it enters the DOM (it's inside @if).
  // Si showPaginator=false el paginator no se renderiza y dataSource.paginator queda null → todos los registros.
  @ViewChild(MatPaginator) set paginator(p: MatPaginator) {
    this.dataSource.paginator = p ?? null;
  }

  @ViewChild('topTrack')  topTrack!:  ElementRef<HTMLDivElement>;
  @ViewChild('topSpacer') topSpacer!: ElementRef<HTMLDivElement>;
  @ViewChild('tableWrap') tableWrap!: ElementRef<HTMLDivElement>;

  readonly dataSource = new MatTableDataSource<Record<string, unknown>>([]);

  /** Field names used as matColumnDef keys. */
  readonly columnFields = computed(() => this.data()?.columns.map(c => c.field) ?? []);

  /** Badges cortos por fuente (igual que pivot-table). */
  private readonly shortLabels: Record<string, string> = {
    gl: 'GL', facturacion: 'FAC', facturacion_detalle: 'DET',
    cartera: 'CART', inventario: 'INV', terceros_saiopen: 'TER',
    productos: 'PROD', cuentas_contables: 'CC',
  };

  /**
   * Labels resueltos con badge de fuente cuando hay conflicto de etiqueta entre fuentes.
   * Cubre los mismos 4 patrones de clave que usa el backend:
   *   - 'tipo'                 (primaria, raw)
   *   - 'sec_facturacion_tipo' (secundaria, anotación)
   *   - 'tipo_sum'             (métrica primaria)
   *   - 'facturacion_tipo_sum' (métrica secundaria)
   * Fallback: label tal como viene del backend si no hay config del usuario.
   */
  private readonly resolvedLabelMap = computed(() => {
    const map = new Map<string, string>();
    const configs = this.fieldConfigs();

    // Detectar etiquetas repetidas entre fuentes
    const labelSources = new Map<string, string[]>();
    for (const fc of configs) {
      if (!labelSources.has(fc.label)) labelSources.set(fc.label, []);
      labelSources.get(fc.label)!.push(fc.source);
    }

    for (const fc of configs) {
      const conflict = (labelSources.get(fc.label)?.length ?? 0) > 1;
      const badge = this.shortLabels[fc.source] ?? fc.source.slice(0, 3).toUpperCase();
      const display = conflict ? `${fc.label} (${badge})` : fc.label;
      const agg = (fc.aggregation ?? 'sum').toLowerCase();

      // Clave raw (solo primera aparición → fuente primaria)
      if (!map.has(fc.field))            map.set(fc.field, display);
      if (!map.has(`${fc.field}_${agg}`)) map.set(`${fc.field}_${agg}`, display);
      // Clave de anotación secundaria
      map.set(`sec_${fc.source}_${fc.field}`, display);
      map.set(`${fc.source}_${fc.field}_${agg}`, display);
    }
    return map;
  });

  /** label map: field → display label (fallback desde el backend) */
  readonly columnLabels = computed(() => {
    const map = new Map<string, string>();
    this.data()?.columns.forEach(c => map.set(c.field, c.label));
    return map;
  });

  /** Mapa: field → formato configurado por el usuario.
   *  Cubre 4 patrones de clave que genera el backend:
   *   - 'debito'           (campo primario)
   *   - 'debito_sum'       (métrica primaria con sufijo de agregación)
   *   - 'sec_facturacion_iva'       (dimensión de fuente secundaria)
   *   - 'facturacion_iva_sum'       (métrica de fuente secundaria) */
  private readonly formatMap = computed(() => {
    const map = new Map<string, BIFieldFormat>();
    this.fieldConfigs().forEach(fc => {
      if (fc.format) {
        const agg = (fc.aggregation ?? 'sum').toLowerCase();
        // Fuente primaria
        map.set(fc.field, fc.format);
        map.set(`${fc.field}_${agg}`, fc.format);
        // Fuente secundaria — dimensión anotada: sec_{source}_{field}
        map.set(`sec_${fc.source}_${fc.field}`, fc.format);
        // Fuente secundaria — métrica anotada: {source}_{field}_{agg}
        map.set(`${fc.source}_${fc.field}_${agg}`, fc.format);
        if (fc.is_calculated) map.set(fc.field, fc.format);
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
      // Actualizar el ancho del spacer cuando cambian los datos (después del render).
      setTimeout(() => this.syncSpacerWidth());
    });
  }

  ngAfterViewInit(): void {
    if (!this.tableWrap) return;
    this.resizeObserver = new ResizeObserver(() => this.syncSpacerWidth());
    this.resizeObserver.observe(this.tableWrap.nativeElement);
  }

  private syncSpacerWidth(): void {
    if (this.topSpacer && this.tableWrap) {
      this.topSpacer.nativeElement.style.minWidth =
        `${this.tableWrap.nativeElement.scrollWidth}px`;
    }
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
    return this.resolvedLabelMap().get(field)
        ?? this.columnLabels().get(field)
        ?? field;
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
