import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  output,
  signal,
  effect,
} from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartType } from 'chart.js';
import {
  ReportBIVisualization,
  ReportBITableResult,
  isTableResult,
  ReportBIExecuteResult,
} from '../../models/report-bi.model';
import { BIFieldConfig } from '../../models/bi-field.model';

const CHART_COLORS = [
  '#1565c0', '#2e7d32', '#e65100', '#6a1b9a',
  '#00838f', '#c62828', '#f9a825', '#283593',
  '#4e342e', '#00695c', '#ad1457', '#1b5e20',
];

@Component({
  selector: 'app-chart-renderer',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DecimalPipe, FormsModule, MatIconModule, MatSelectModule, MatFormFieldModule, BaseChartDirective],
  templateUrl: './chart-renderer.component.html',
  styleUrl: './chart-renderer.component.scss',
})
export class ChartRendererComponent {
  readonly data = input<ReportBIExecuteResult | null>(null);
  readonly visualization = input<ReportBIVisualization>('bar');
  readonly fields = input<BIFieldConfig[]>([]);
  readonly loading = input(false);
  readonly chartClick = output<{ label: string; datasetIndex: number; index: number }>();

  /** Campo seleccionado para el Eje X (dimensión). Por defecto: primera dimensión. */
  readonly xAxisField = signal<string>('');

  readonly dimensions = computed(() => this.fields().filter(f => f.role === 'dimension'));

  readonly isKpi = computed(() => this.visualization() === 'kpi');
  readonly isChart = computed(() => !this.isKpi() && this.visualization() !== 'table' && this.visualization() !== 'pivot');

  constructor() {
    // Cuando cambian los campos disponibles, resetear xAxisField si el campo ya no existe
    effect(() => {
      const dims = this.dimensions();
      if (dims.length > 0 && !dims.find(d => d.field === this.xAxisField())) {
        this.xAxisField.set(dims[0].field);
      }
    });
  }

  /** KPI data: suma TODOS los valores de todas las filas (no solo rows[0]) */
  readonly kpiData = computed(() => {
    const d = this.data();
    if (!d || !isTableResult(d) || d.rows.length === 0) return [];
    const metrics = this.fields().filter(f => f.role === 'metric');
    return metrics.map((m, i) => {
      const aggKey = `${m.field}_${(m.aggregation ?? 'sum').toLowerCase()}`;
      const total = d.rows.reduce((sum, row) => {
        const val = ((row[aggKey] ?? row[m.field]) as number) || 0;
        return sum + val;
      }, 0);
      return {
        label: m.label,
        value: total,
        icon: this.kpiIcon(i),
        color: CHART_COLORS[i % CHART_COLORS.length],
      };
    });
  });

  /** Chart.js config for bar/line/pie/area/waterfall */
  readonly chartConfig = computed((): ChartConfiguration | null => {
    const d = this.data();
    const viz = this.visualization();
    if (!d || !isTableResult(d) || d.rows.length === 0) return null;
    if (viz === 'kpi' || viz === 'table' || viz === 'pivot') return null;

    const dimensions = this.dimensions();
    const metrics = this.fields().filter(f => f.role === 'metric');
    if (dimensions.length === 0 || metrics.length === 0) return null;

    const labelField = this.xAxisField() || dimensions[0].field;
    const labels = d.rows.map(r => String(r[labelField] ?? ''));

    if (viz === 'pie') {
      return this.buildPieConfig(labels, d.rows, metrics);
    }
    if (viz === 'waterfall') {
      return this.buildWaterfallConfig(labels, d.rows, metrics);
    }
    return this.buildAxisConfig(viz, labels, d.rows, metrics);
  });

  readonly chartType = computed((): ChartType => {
    const viz = this.visualization();
    if (viz === 'area') return 'line';
    if (viz === 'waterfall') return 'bar';
    if (viz === 'pie') return 'pie';
    return viz as ChartType;
  });

  onChartClick(event: Record<string, unknown>): void {
    const active = event['active'] as Array<{ datasetIndex: number; index: number }> | undefined;
    if (!active?.length) return;
    const { datasetIndex, index } = active[0];
    const d = this.data();
    if (!d || !isTableResult(d)) return;
    const dims = this.fields().filter(f => f.role === 'dimension');
    const label = String(d.rows[index]?.[dims[0]?.field] ?? '');
    this.chartClick.emit({ label, datasetIndex, index });
  }

  private buildAxisConfig(
    viz: string,
    labels: string[],
    rows: Record<string, unknown>[],
    metrics: BIFieldConfig[],
  ): ChartConfiguration {
    const isArea = viz === 'area';
    const datasets = metrics.map((m, i) => {
      const key = m.field;
      const aggKey = `${m.field}_${(m.aggregation ?? 'sum').toLowerCase()}`;
      return {
        label: m.label,
        data: rows.map(r => (r[aggKey] ?? r[key] ?? 0) as number),
        backgroundColor: CHART_COLORS[i % CHART_COLORS.length] + (isArea ? '40' : ''),
        borderColor: CHART_COLORS[i % CHART_COLORS.length],
        fill: isArea,
        tension: isArea ? 0.3 : 0,
      };
    });

    return {
      type: viz === 'area' ? 'line' : viz as ChartType,
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top' },
        },
        scales: {
          y: { beginAtZero: true },
        },
      },
    };
  }

  private buildPieConfig(
    labels: string[],
    rows: Record<string, unknown>[],
    metrics: BIFieldConfig[],
  ): ChartConfiguration {
    const m = metrics[0];
    const aggKey = `${m.field}_${(m.aggregation ?? 'sum').toLowerCase()}`;
    const data = rows.map(r => (r[aggKey] ?? r[m.field] ?? 0) as number);
    const colors = labels.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]);

    return {
      type: 'pie',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right' },
        },
      },
    };
  }

  private buildWaterfallConfig(
    labels: string[],
    rows: Record<string, unknown>[],
    metrics: BIFieldConfig[],
  ): ChartConfiguration {
    const m = metrics[0];
    const aggKey = `${m.field}_${(m.aggregation ?? 'sum').toLowerCase()}`;
    const values = rows.map(r => (r[aggKey] ?? r[m.field] ?? 0) as number);

    // Build floating bars: each bar starts where previous ended
    const bases: number[] = [];
    const tops: number[] = [];
    let running = 0;
    for (const v of values) {
      bases.push(running);
      running += v;
      tops.push(running);
    }
    // Add total bar
    labels.push('Total');
    const floatingData = bases.map((b, i) => [b, tops[i]]);
    floatingData.push([0, running]);

    const bgColors: string[] = values.map(v => v >= 0 ? '#2e7d32' : '#c62828');
    bgColors.push('#1565c0');

    return {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: m.label,
          data: floatingData as unknown as number[],
          backgroundColor: bgColors,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const raw = ctx.raw as [number, number];
                return `${m.label}: ${(raw[1] - raw[0]).toLocaleString()}`;
              },
            },
          },
        },
        scales: {
          y: { beginAtZero: true },
        },
      },
    };
  }

  private kpiIcon(index: number): string {
    const icons = ['trending_up', 'payments', 'account_balance', 'analytics', 'speed', 'monitoring'];
    return icons[index % icons.length];
  }
}
