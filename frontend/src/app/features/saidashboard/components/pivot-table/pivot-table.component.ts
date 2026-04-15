import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  afterEveryRender,
  computed,
  input,
  output,
  viewChild,
} from '@angular/core';
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
  imports: [MatProgressBarModule],
  templateUrl: './pivot-table.component.html',
  styleUrl: './pivot-table.component.scss',
})
export class PivotTableComponent {
  readonly data = input<ReportBIPivotResult | null>(null);
  readonly loading = input(false);
  readonly fieldConfigs = input<BIFieldConfig[]>([]);
  readonly cellClick = output<PivotCellClick>();

  // ── Scroll sincronizado (top + bottom) ──────────────────────────
  private readonly tableWrap = viewChild<ElementRef<HTMLDivElement>>('tableWrap');
  private readonly topBar    = viewChild<ElementRef<HTMLDivElement>>('topBar');
  private readonly phantom   = viewChild<ElementRef<HTMLDivElement>>('phantom');

  constructor() {
    // Sincronizar el ancho del phantom con el contenido real de la tabla
    afterEveryRender(() => {
      const wrap = this.tableWrap()?.nativeElement;
      const ph   = this.phantom()?.nativeElement;
      if (wrap && ph) {
        ph.style.width = wrap.scrollWidth + 'px';
      }
    });
  }

  onTableScroll(event: Event): void {
    const wrap = event.target as HTMLDivElement;
    const top  = this.topBar()?.nativeElement;
    if (top) top.scrollLeft = wrap.scrollLeft;
  }

  onTopScroll(event: Event): void {
    const top  = event.target as HTMLDivElement;
    const wrap = this.tableWrap()?.nativeElement;
    if (wrap) wrap.scrollLeft = top.scrollLeft;
  }

  // ── Formato ────────────────────────────────────────────────────

  private readonly formatMap = computed(() => {
    const map = new Map<string, BIFieldFormat>();
    this.fieldConfigs().forEach(fc => {
      if (fc.format) {
        const agg = (fc.aggregation ?? 'sum').toLowerCase();
        // Fuente primaria
        map.set(fc.field, fc.format);
        map.set(`${fc.field}_${agg}`, fc.format);
        // Fuente secundaria — dimensión: sec_{source}_{field}
        map.set(`sec_${fc.source}_${fc.field}`, fc.format);
        // Fuente secundaria — métrica: {source}_{field}_{agg}
        map.set(`${fc.source}_${fc.field}_${agg}`, fc.format);
        if (fc.is_calculated) map.set(fc.field, fc.format);
      }
    });
    return map;
  });

  readonly noColumnMode = computed(() => this.data()?.no_column_mode ?? false);

  // ── Mapa field-name → label configurado por el usuario ─────────
  // Incluye el patrón de anotación secundaria: sec_{source}_{field}
  // Solo muestra badge de fuente cuando la misma etiqueta aparece en varias fuentes.
  private readonly shortLabels: Record<string, string> = {
    gl: 'GL', facturacion: 'FAC', facturacion_detalle: 'DET',
    cartera: 'CART', inventario: 'INV', terceros_saiopen: 'TER',
    productos: 'PROD', cuentas_contables: 'CC',
  };

  private readonly dimLabelMap = computed(() => {
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
      // Clave raw: solo la primera config con este field name (fuente primaria).
      // La secundaria usa únicamente su clave sec_*, para no sobreescribir la primaria.
      if (!map.has(fc.field)) {
        map.set(fc.field, display);
      }
      // Clave de anotación secundaria: sec_{source}_{field}
      map.set(`sec_${fc.source}_${fc.field}`, display);
    }
    return map;
  });

  getDimLabel(fieldName: string): string {
    return this.dimLabelMap().get(fieldName) ?? fieldName;
  }

  readonly rowDimFields = computed(() => {
    const d = this.data();
    if (!d || d.row_headers.length === 0) return [];
    return Object.keys(d.row_headers[0]);
  });

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

  readonly valueAlias = computed(() => this.data()?.value_aliases?.[0] ?? '');
  readonly valueAliases = computed(() => this.data()?.value_aliases ?? []);

  readonly rowData = computed(() => {
    const d = this.data();
    if (!d) return [];
    return d.row_headers.map(h => ({ headers: h, key: this.headerToKey(h) }));
  });

  readonly hasData = computed(() => {
    const d = this.data();
    return d !== null && d.row_headers.length > 0;
  });

  // ── Labels ─────────────────────────────────────────────────────

  getMetricLabel(alias: string): string {
    const d = this.data();
    if (d?.value_labels?.[alias]) return d.value_labels[alias];
    const fc = this.fieldConfigs().find(f => {
      const agg = (f.aggregation ?? 'SUM').toLowerCase();
      return `${f.field}_${agg}` === alias;
    });
    return fc?.label ?? alias;
  }

  // ── Valores modo sin-columna ────────────────────────────────────

  getMetricValue(rowKey: string, alias: string): number | null {
    const totals = this.data()?.row_totals[rowKey];
    return totals ? (totals[alias] as number) ?? null : null;
  }

  getGrandTotalForAlias(alias: string): number | null {
    const gt = this.data()?.grand_total;
    return gt ? (gt[alias] as number) ?? null : null;
  }

  // ── Valores modo con-columna ────────────────────────────────────

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

  getMetricFormat(alias: string): BIFieldFormat {
    return this.formatMap().get(alias) ?? 'number';
  }

  formatValue(value: number | null, alias: string): string {
    const fmt = this.getMetricFormat(alias);
    if (value === null) return fmt === 'currency' ? '$ 0' : '—';
    const n = value.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    return fmt === 'currency' ? `$ ${n}` : n;
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
