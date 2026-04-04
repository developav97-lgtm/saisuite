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

  readonly chartContainer = viewChild<ElementRef<HTMLDivElement>>('chartContainer');

  readonly noData = computed(() => {
    const ds = this.datasets();
    return !ds || ds.length === 0 || ds.every(d => d.data.length === 0);
  });

  private chartInstance: unknown = null;
  private resizeObserver: ResizeObserver | null = null;

  constructor() {
    // Render chart when inputs change
    effect(() => {
      const container = this.chartContainer();
      const type = this.chartType();
      const lbls = this.labels();
      const ds = this.datasets();
      const isLoading = this.loading();

      if (container && !isLoading && ds.length > 0) {
        this.renderChart(container.nativeElement, type, lbls, ds);
      }
    });
  }

  ngOnDestroy(): void {
    this.disposeChart();
    this.resizeObserver?.disconnect();
  }

  onFullscreen(): void {
    const el = this.chartContainer()?.nativeElement;
    if (el?.requestFullscreen) {
      el.requestFullscreen();
    }
  }

  private async renderChart(
    container: HTMLDivElement,
    type: ChartType,
    labels: string[],
    datasets: DatasetItem[],
  ): Promise<void> {
    const echarts = await import('echarts');
    this.disposeChart();

    const isDark = document.body.classList.contains('dark-theme');
    const chart = echarts.init(container, isDark ? 'dark' : undefined);
    this.chartInstance = chart;

    const textColor = isDark ? '#e2e8f0' : '#1a202c';
    const mutedColor = isDark ? '#718096' : '#a0aec0';

    const option = this.buildOption(type, labels, datasets, textColor, mutedColor);
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
          tooltip: { trigger: 'axis' },
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
            data: ds.data,
            barMaxWidth: 40,
            itemStyle: { borderRadius: [4, 4, 0, 0] },
          })),
        };

      case 'line':
      case 'area':
        return {
          color: colorPalette,
          textStyle: baseTextStyle,
          tooltip: { trigger: 'axis' },
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
            data: ds.data,
            smooth: true,
            areaStyle: type === 'area' ? { opacity: 0.15 } : undefined,
          })),
        };

      case 'pie':
        return {
          color: colorPalette,
          textStyle: baseTextStyle,
          tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
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
              value: datasets[0]?.data[i] ?? 0,
            })),
          }],
        };

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
          tooltip: { trigger: 'axis' },
          xAxis: { type: 'category', data: labels, axisLabel },
          yAxis: { type: 'value', axisLabel },
          series: datasets.map(ds => ({
            name: ds.label,
            type: 'bar',
            data: ds.data,
          })),
        };
    }
  }

  private buildWaterfallOption(
    labels: string[],
    datasets: DatasetItem[],
    textColor: string,
    mutedColor: string,
  ): Record<string, unknown> {
    const data = datasets[0]?.data ?? [];
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

    return {
      textStyle: { color: textColor },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
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

  private disposeChart(): void {
    if (this.chartInstance) {
      (this.chartInstance as { dispose: () => void }).dispose();
      this.chartInstance = null;
    }
  }
}
