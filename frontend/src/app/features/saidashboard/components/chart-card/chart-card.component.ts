import {
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  ElementRef,
  input,
  OnDestroy,
  signal,
  viewChild,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ChartType } from '../../models/dashboard.model';
import { DatasetItem } from '../../models/report-filter.model';

/** Lightweight ECharts wrapper using dynamic import to avoid bundle bloat. */
@Component({
  selector: 'app-chart-card',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatIconModule,
    MatButtonModule,
    MatMenuModule,
    MatTooltipModule,
    MatProgressBarModule,
  ],
  template: `
    <div class="cc-card">
      <div class="cc-header">
        <h3 class="cc-title">{{ title() }}</h3>
        @if (showMenu()) {
          <button mat-icon-button [matMenuTriggerFor]="cardMenu" matTooltip="Opciones">
            <mat-icon>more_vert</mat-icon>
          </button>
          <mat-menu #cardMenu="matMenu">
            <button mat-menu-item (click)="onFullscreen()">
              <mat-icon>fullscreen</mat-icon> Pantalla completa
            </button>
          </mat-menu>
        }
      </div>

      @if (loading()) {
        <mat-progress-bar mode="indeterminate" class="cc-progress" />
      }

      <div class="cc-body">
        @if (!loading() && noData()) {
          <div class="cc-no-data">
            <mat-icon>bar_chart</mat-icon>
            <p>Sin datos para mostrar</p>
          </div>
        } @else {
          <div #chartContainer class="cc-chart-container"></div>
        }
      </div>
    </div>
  `,
  styles: [`
    .cc-card {
      background: var(--sc-surface-card);
      border: 1px solid var(--sc-surface-border);
      border-radius: var(--sc-radius);
      box-shadow: var(--sc-shadow-sm);
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
    }

    .cc-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.75rem 1rem 0;
      gap: 0.5rem;
    }

    .cc-title {
      font-size: 0.8125rem;
      font-weight: 600;
      color: var(--sc-text-color);
      margin: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      flex: 1;
    }

    .cc-progress {
      margin: 0.5rem 0 -4px;
    }

    .cc-body {
      flex: 1;
      padding: 0.5rem;
      min-height: 200px;
      position: relative;
    }

    .cc-chart-container {
      width: 100%;
      height: 100%;
      min-height: 200px;
    }

    .cc-no-data {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      min-height: 200px;
      color: var(--sc-text-muted);

      mat-icon {
        font-size: 2rem;
        width: 2rem;
        height: 2rem;
        opacity: 0.3;
        margin-bottom: 0.5rem;
      }

      p {
        font-size: 0.8125rem;
        margin: 0;
      }
    }
  `],
})
export class ChartCardComponent implements OnDestroy {
  readonly chartType = input.required<ChartType>();
  readonly labels = input<string[]>([]);
  readonly datasets = input<DatasetItem[]>([]);
  readonly title = input<string>('');
  readonly loading = input<boolean>(false);
  readonly showMenu = input<boolean>(true);
  readonly isMonthly = input<boolean>(false);

  readonly chartContainer = viewChild<ElementRef<HTMLDivElement>>('chartContainer');

  readonly noData = computed(() => {
    const ds = this.datasets();
    return !ds || ds.length === 0 || ds.every(d => d.data.length === 0);
  });

  private chartInstance: unknown = null;
  private resizeObserver: ResizeObserver | null = null;
  private fullscreenHandler: (() => void) | null = null;

  constructor() {
    // Render chart when inputs change
    effect(() => {
      const container = this.chartContainer();
      const type = this.chartType();
      const lbls = this.labels();
      const ds = this.datasets();
      const isLoading = this.loading();
      const monthly = this.isMonthly();

      if (container && !isLoading && ds.length > 0) {
        this.renderChart(container.nativeElement, type, lbls, ds, monthly);
      }
    });
  }

  ngOnDestroy(): void {
    this.disposeChart();
    this.resizeObserver?.disconnect();
    if (this.fullscreenHandler) {
      document.removeEventListener('fullscreenchange', this.fullscreenHandler);
    }
  }

  onFullscreen(): void {
    const el = this.chartContainer()?.nativeElement;
    if (!el?.requestFullscreen) return;

    // Registrar handler para forzar resize al salir de fullscreen
    if (!this.fullscreenHandler) {
      this.fullscreenHandler = () => {
        const isFullscreen = !!document.fullscreenElement;
        if (!isFullscreen) {
          // Limpiar height inline que algunos browsers inyectan al salir
          el.style.height = '';
        }
        // Forzar resize del chart en ambos casos (entrar y salir)
        const chart = this.chartInstance as { resize?: () => void } | null;
        // requestAnimationFrame da tiempo al browser de aplicar los estilos antes del resize
        requestAnimationFrame(() => chart?.resize?.());
      };
      document.addEventListener('fullscreenchange', this.fullscreenHandler);
    }

    el.requestFullscreen();
  }

  private async renderChart(
    container: HTMLDivElement,
    type: ChartType,
    labels: string[],
    datasets: DatasetItem[],
    isMonthly = false,
  ): Promise<void> {
    const echarts = await import('echarts');
    this.disposeChart();

    const isDark = document.body.classList.contains('dark-theme');
    const chart = echarts.init(container, isDark ? 'dark' : undefined);
    this.chartInstance = chart;

    const textColor = isDark ? '#e2e8f0' : '#1a202c';
    const mutedColor = isDark ? '#718096' : '#a0aec0';

    const option = isMonthly && type === 'bar'
      ? this.buildMonthlyBarOption(labels, datasets, textColor, mutedColor)
      : this.buildOption(type, labels, datasets, textColor, mutedColor);
    chart.setOption(option);

    // Observe container resize for responsiveness
    this.resizeObserver?.disconnect();
    this.resizeObserver = new ResizeObserver(() => {
      (chart as { resize: () => void }).resize();
    });
    this.resizeObserver.observe(container);
  }

  private buildOption(
    type: ChartType,
    labels: string[],
    datasets: DatasetItem[],
    textColor: string,
    mutedColor: string,
  ): Record<string, unknown> {
    const baseTextStyle = { color: textColor, fontSize: 12 };
    const axisLabel = { color: mutedColor, fontSize: 11 };

    const colorPalette = [
      '#1565c0', '#42a5f5', '#0d47a1', '#90caf9',
      '#2e7d32', '#66bb6a', '#f57f17', '#ffa726',
      '#c62828', '#ef5350', '#6d28d9', '#a78bfa',
    ];

    switch (type) {
      case 'bar':
        return {
          color: colorPalette,
          textStyle: baseTextStyle,
          tooltip: { trigger: 'axis', confine: true, formatter: this.axisFormatter() },
          legend: {
            show: datasets.length > 1,
            bottom: 0,
            textStyle: { color: mutedColor },
          },
          grid: { left: '3%', right: '4%', bottom: datasets.length > 1 ? '15%' : '8%', top: '8%', containLabel: true },
          xAxis: { type: 'category', data: labels, axisLabel },
          yAxis: { type: 'value', axisLabel },
          series: datasets.map(ds => ({
            name: ds.label,
            type: 'bar',
            data: ds.data.map(Number),
            barMaxWidth: 40,
            itemStyle: { borderRadius: [4, 4, 0, 0] },
          })),
        };

      case 'line':
      case 'area':
        return {
          color: colorPalette,
          textStyle: baseTextStyle,
          tooltip: { trigger: 'axis', confine: true, formatter: this.axisFormatter() },
          legend: {
            show: datasets.length > 1,
            bottom: 0,
            textStyle: { color: mutedColor },
          },
          grid: { left: '3%', right: '4%', bottom: datasets.length > 1 ? '15%' : '8%', top: '8%', containLabel: true },
          xAxis: { type: 'category', data: labels, axisLabel },
          yAxis: { type: 'value', axisLabel },
          series: datasets.map(ds => ({
            name: ds.label,
            type: 'line',
            data: ds.data.map(Number),
            smooth: true,
            areaStyle: type === 'area' ? { opacity: 0.15 } : undefined,
          })),
        };

      case 'pie':
        return {
          color: colorPalette,
          textStyle: baseTextStyle,
          tooltip: { trigger: 'item', confine: true, formatter: '{b}: {c} ({d}%)' },
          legend: {
            orient: 'vertical',
            right: '5%',
            top: 'center',
            textStyle: { color: mutedColor },
          },
          series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['40%', '50%'],
            avoidLabelOverlap: true,
            itemStyle: { borderRadius: 6, borderColor: 'transparent', borderWidth: 2 },
            label: { show: false },
            emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
            data: labels.map((l, i) => ({
              name: l,
              value: Number(datasets[0]?.data[i] ?? 0),
            })),
          }],
        };

      case 'table':
        return this.buildTableOption(labels, datasets, textColor, mutedColor);

      case 'waterfall':
        return this.buildWaterfallOption(labels, datasets, textColor, mutedColor);

      case 'gauge':
        return {
          textStyle: baseTextStyle,
          series: [{
            type: 'gauge',
            detail: { formatter: '{value}%', fontSize: 20, color: textColor },
            data: [{ value: datasets[0]?.data[0] ?? 0, name: datasets[0]?.label ?? '' }],
            axisLine: {
              lineStyle: {
                width: 20,
                color: [
                  [0.3, '#c62828'],
                  [0.7, '#f57f17'],
                  [1, '#2e7d32'],
                ],
              },
            },
            pointer: { width: 5 },
            title: { color: mutedColor },
          }],
        };

      default:
        return {
          color: colorPalette,
          textStyle: baseTextStyle,
          tooltip: { trigger: 'axis', confine: true, formatter: this.axisFormatter() },
          xAxis: { type: 'category', data: labels, axisLabel },
          yAxis: { type: 'value', axisLabel },
          series: datasets.map(ds => ({
            name: ds.label,
            type: 'bar',
            data: ds.data.map(Number),
          })),
        };
    }
  }

  private buildTableOption(
    labels: string[],
    datasets: DatasetItem[],
    textColor: string,
    mutedColor: string,
  ): Record<string, unknown> {
    const colorPalette = [
      '#1565c0', '#42a5f5', '#0d47a1', '#90caf9',
      '#2e7d32', '#66bb6a', '#f57f17', '#ffa726',
    ];
    const formatCOP = (value: number): string =>
      new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);

    return {
      color: colorPalette,
      textStyle: { color: textColor, fontSize: 12 },
      tooltip: {
        trigger: 'axis',
        confine: true,
        axisPointer: { type: 'shadow' },
        formatter: (params: { seriesName: string; value: number; name: string }[]) =>
          `${params[0]?.name ?? ''}<br/>` +
          params.map(p => `${p.seriesName}: ${formatCOP(p.value)}`).join('<br/>'),
      },
      legend: {
        show: datasets.length > 1,
        bottom: 0,
        textStyle: { color: mutedColor },
      },
      grid: {
        left: '3%', right: '4%',
        bottom: datasets.length > 1 ? '15%' : '8%',
        top: '8%',
        containLabel: true,
      },
      xAxis: { type: 'value', axisLabel: { color: mutedColor, fontSize: 11 } },
      yAxis: {
        type: 'category',
        data: [...labels].reverse(),
        axisLabel: {
          color: mutedColor,
          fontSize: 11,
          width: 120,
          overflow: 'truncate',
        },
      },
      series: datasets.map(ds => ({
        name: ds.label,
        type: 'bar',
        data: [...ds.data].map(Number).reverse(),
        barMaxWidth: 24,
        itemStyle: { borderRadius: [0, 4, 4, 0] },
        label: {
          show: true,
          position: 'right',
          formatter: (p: { value: number }) => formatCOP(p.value),
          fontSize: 10,
          color: mutedColor,
        },
      })),
    };
  }

  private buildMonthlyBarOption(
    labels: string[],
    datasets: DatasetItem[],
    textColor: string,
    mutedColor: string,
  ): Record<string, unknown> {
    const colorPalette = [
      '#1565c0', '#42a5f5', '#0d47a1', '#90caf9',
      '#2e7d32', '#66bb6a', '#f57f17', '#ffa726',
    ];
    const formatCOP = (value: number): string =>
      new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);

    return {
      color: colorPalette,
      textStyle: { color: textColor, fontSize: 12 },
      tooltip: {
        trigger: 'axis',
        confine: true,
        formatter: (params: { seriesName: string; value: number }[]) =>
          params.map(p => `${p.seriesName}: ${formatCOP(p.value)}`).join('<br/>'),
      },
      legend: {
        show: datasets.length > 1,
        bottom: 0,
        textStyle: { color: mutedColor },
      },
      grid: {
        left: '3%', right: '4%',
        bottom: datasets.length > 1 ? '25%' : '18%',
        top: '8%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: labels,
        axisLabel: { color: mutedColor, fontSize: 11, rotate: 45 },
      },
      yAxis: { type: 'value', axisLabel: { color: mutedColor, fontSize: 11 } },
      series: datasets.map(ds => ({
        name: ds.label,
        type: 'bar',
        data: ds.data.map(Number),
        barMaxWidth: 20,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      })),
    };
  }

  private buildWaterfallOption(
    labels: string[],
    datasets: DatasetItem[],
    textColor: string,
    mutedColor: string,
  ): Record<string, unknown> {
    const data = (datasets[0]?.data ?? []).map(Number);
    const helperData: (number | string)[] = [];
    const posData: (number | string)[] = [];
    const negData: (number | string)[] = [];
    let running = 0;

    for (let i = 0; i < data.length; i++) {
      const val = data[i];
      if (i === 0 || i === data.length - 1) {
        helperData.push(0);
        posData.push(val);
        negData.push('-');
      } else if (val >= 0) {
        helperData.push(running);
        posData.push(val);
        negData.push('-');
      } else {
        helperData.push(running + val);
        posData.push('-');
        negData.push(Math.abs(val));
      }
      running += val;
    }

    const formatCOPw = (value: number): string =>
      new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);

    return {
      textStyle: { color: textColor },
      tooltip: {
        trigger: 'axis',
        confine: true,
        axisPointer: { type: 'shadow' },
        formatter: (params: { seriesName: string; value: number | string }[]) => {
          const visible = params.filter(p => p.seriesName !== 'Invisible' && p.value !== '-');
          return visible.map(p => `${p.seriesName}: ${formatCOPw(Number(p.value))}`).join('<br/>');
        },
      },
      grid: { left: '3%', right: '4%', bottom: '8%', top: '8%', containLabel: true },
      xAxis: { type: 'category', data: labels, axisLabel: { color: mutedColor } },
      yAxis: { type: 'value', axisLabel: { color: mutedColor } },
      series: [
        {
          name: 'Invisible',
          type: 'bar',
          stack: 'waterfall',
          data: helperData,
          itemStyle: { borderColor: 'transparent', color: 'transparent' },
          emphasis: { itemStyle: { borderColor: 'transparent', color: 'transparent' } },
          tooltip: { show: false },
        },
        {
          name: 'Positivo',
          type: 'bar',
          stack: 'waterfall',
          data: posData,
          itemStyle: { color: '#2e7d32', borderRadius: [4, 4, 0, 0] },
        },
        {
          name: 'Negativo',
          type: 'bar',
          stack: 'waterfall',
          data: negData,
          itemStyle: { color: '#c62828', borderRadius: [4, 4, 0, 0] },
        },
      ],
    };
  }

  /** Formateador de tooltip COP para ejes (bar/line/area). */
  private axisFormatter() {
    const fmt = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
    return (params: { seriesName: string; value: number; name: string }[]) => {
      const header = params[0]?.name ?? '';
      const rows = params.map(p => `${p.seriesName}: ${fmt.format(Number(p.value))}`).join('<br/>');
      return header ? `${header}<br/>${rows}` : rows;
    };
  }

  private disposeChart(): void {
    if (this.chartInstance) {
      (this.chartInstance as { dispose: () => void }).dispose();
      this.chartInstance = null;
    }
  }
}
