import {
  Component,
  OnDestroy,
  AfterViewInit,
  ChangeDetectionStrategy,
  signal,
  computed,
  input,
  ViewChild,
  ElementRef,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin, Subscription } from 'rxjs';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Chart } from 'chart.js';
import { AnalyticsService } from '../../../services/analytics.service';
import { ToastService } from '../../../../../core/services/toast.service';
import {
  ProjectKPIs,
  TaskDistribution,
  VelocityDataPoint,
  BurnDownData,
  ResourceUtilization,
} from '../../../models/analytics.model';

@Component({
  selector: 'app-project-analytics-dashboard',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  templateUrl: './project-analytics-dashboard.component.html',
  styleUrl: './project-analytics-dashboard.component.scss',
})
export class ProjectAnalyticsDashboardComponent implements AfterViewInit, OnDestroy {
  private readonly analyticsService = inject(AnalyticsService);
  private readonly toast       = inject(ToastService);

  readonly projectId = input.required<string>();
  /** Set to true by the parent when this tab becomes the active tab. */
  readonly tabActive = input(false);

  readonly loading = signal(false);
  readonly kpis = signal<ProjectKPIs | null>(null);
  readonly taskDistribution = signal<TaskDistribution | null>(null);
  readonly velocityData = signal<VelocityDataPoint[]>([]);
  readonly burnDownData = signal<BurnDownData | null>(null);
  readonly resourceUtilization = signal<ResourceUtilization[]>([]);

  @ViewChild('burnDownCanvas') burnDownCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('velocityCanvas') velocityCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('taskDistCanvas') taskDistCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('resourceCanvas') resourceCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('chartsGrid')    chartsGrid!: ElementRef<HTMLDivElement>;

  readonly completionClass   = computed(() => this.kpiClass(this.kpis()?.completion_rate ?? 0));
  readonly onTimeClass       = computed(() => this.kpiClass(this.kpis()?.on_time_rate ?? 0));
  readonly budgetClass_      = computed(() => this.budgetClass(this.kpis()?.budget_variance ?? null));
  readonly budgetVarianceFmt = computed(() => this.formatVariance(this.kpis()?.budget_variance ?? null));

  private charts: Chart[] = [];
  private loadSub: Subscription | null = null;
  private exportSub: Subscription | null = null;
  private dataReady = false;
  private containerVisible = false;
  private resizeObserver: ResizeObserver | null = null;

  ngAfterViewInit(): void {
    this.loadData();
    this.setupResizeObserver();
  }

  ngOnDestroy(): void {
    this.destroyCharts();
    this.resizeObserver?.disconnect();
    this.loadSub?.unsubscribe();
    this.exportSub?.unsubscribe();
  }

  private setupResizeObserver(): void {
    const el = this.chartsGrid?.nativeElement;
    if (!el) return;
    this.resizeObserver = new ResizeObserver(entries => {
      const width = entries[0]?.contentRect.width ?? 0;
      if (width > 0) {
        this.containerVisible = true;
        if (this.dataReady) {
          this.drawCharts();
        }
      }
    });
    this.resizeObserver.observe(el);
  }

  loadData(): void {
    this.loadSub?.unsubscribe();
    this.loading.set(true);
    this.dataReady = false;
    this.destroyCharts();
    const id = this.projectId();

    this.loadSub = forkJoin({
      kpis:         this.analyticsService.getKPIs(id),
      distribution: this.analyticsService.getTaskDistribution(id),
      velocity:     this.analyticsService.getVelocity(id),
      burnDown:     this.analyticsService.getBurnDown(id),
      resources:    this.analyticsService.getResourceUtilization(id),
    }).subscribe({
      next: (data) => {
        this.kpis.set(data.kpis);
        this.taskDistribution.set(data.distribution);
        this.velocityData.set(data.velocity.data);
        this.burnDownData.set(data.burnDown);
        this.resourceUtilization.set(data.resources);
        this.loading.set(false);
        this.dataReady = true;
        // Draw if the container is already visible (ResizeObserver already fired).
        // Otherwise ResizeObserver will call drawCharts() once the container has dimensions.
        if (this.containerVisible) {
          this.drawCharts();
        }
      },
      error: () => {
        this.loading.set(false);
        this.toast.error('Error al cargar analytics');
      },
    });
  }

  /** Public — called by the refresh button */
  redrawCharts(): void {
    this.loadData();
  }

  kpiClass(value: number): string {
    if (value >= 75) return 'pad-kpi__trend--up';
    if (value >= 50) return 'pad-kpi__trend--warn';
    return 'pad-kpi__trend--danger';
  }

  budgetClass(variance: number | null): string {
    if (variance === null) return 'pad-kpi__trend--neutral';
    if (variance <= 0) return 'pad-kpi__trend--up';
    if (variance <= 10) return 'pad-kpi__trend--warn';
    return 'pad-kpi__trend--danger';
  }

  formatVariance(v: number | null): string {
    if (v === null) return 'N/A';
    return v >= 0 ? `+${v.toFixed(1)}%` : `${v.toFixed(1)}%`;
  }

  private destroyCharts(): void {
    this.charts.forEach(c => c.destroy());
    this.charts = [];
  }

  drawCharts(): void {
    this.destroyCharts();

    const burnDown  = this.burnDownData();
    const velocity  = this.velocityData();
    const dist      = this.taskDistribution();
    const resources = this.resourceUtilization();

    if (!burnDown && !velocity.length && !dist && !resources.length) return;

    // Set explicit pixel dimensions from the actual DOM container.
    // Use || (not ??) so that 0 also falls back to the default.
    const setSize = (canvas: HTMLCanvasElement) => {
      const box = canvas.closest('.pad-chart-container')?.getBoundingClientRect();
      canvas.width  = Math.round(box?.width  || 560);
      canvas.height = Math.round(box?.height || 280);
    };

    if (this.burnDownCanvas?.nativeElement && burnDown) {
      setSize(this.burnDownCanvas.nativeElement);
      this.charts.push(this.buildBurnDownChart(burnDown));
    }
    if (this.velocityCanvas?.nativeElement && velocity.length) {
      setSize(this.velocityCanvas.nativeElement);
      this.charts.push(this.buildVelocityChart(velocity));
    }
    if (this.taskDistCanvas?.nativeElement && dist) {
      setSize(this.taskDistCanvas.nativeElement);
      this.charts.push(this.buildTaskDistChart(dist));
    }
    if (this.resourceCanvas?.nativeElement && resources.length) {
      setSize(this.resourceCanvas.nativeElement);
      this.charts.push(this.buildResourceChart(resources));
    }
  }

  private buildBurnDownChart(data: BurnDownData): Chart {
    return new Chart(this.burnDownCanvas.nativeElement, {
      type: 'line',
      data: {
        labels: data.data_points.map(p => p.week_label),
        datasets: [
          { label: 'Ideal', data: data.data_points.map(p => p.hours_ideal),
            borderColor: '#9E9E9E', borderDash: [5,5], pointRadius: 0, fill: false },
          { label: 'Estimadas restantes', data: data.data_points.map(p => p.hours_remaining),
            borderColor: '#1976d2', backgroundColor: 'rgba(25,118,210,0.08)', fill: true, tension: 0.3 },
          { label: 'Acumuladas reales', data: data.data_points.map(p => p.hours_actual_cumulative),
            borderColor: '#4CAF50', fill: false, tension: 0.3 },
        ],
      },
      options: {
        responsive: false,
        scales: { y: { beginAtZero: true, title: { display: true, text: 'Horas' } } },
        plugins: { legend: { position: 'top' } },
      },
    });
  }

  private buildVelocityChart(data: VelocityDataPoint[]): Chart {
    const avg = data.reduce((s, p) => s + p.tasks_completed, 0) / data.length;
    return new Chart(this.velocityCanvas.nativeElement, {
      type: 'bar',
      data: {
        labels: data.map(p => p.week_label),
        datasets: [
          { label: 'Tareas completadas', data: data.map(p => p.tasks_completed),
            backgroundColor: data.map(p => p.tasks_completed >= avg ? '#4CAF50' : '#F44336') },
          { label: 'Media', data: data.map(() => avg), type: 'line' as const,
            borderColor: '#FFC107', borderDash: [4,4], pointRadius: 0, fill: false },
        ],
      },
      options: {
        responsive: false,
        scales: { y: { beginAtZero: true } },
        plugins: { legend: { position: 'top' } },
      },
    });
  }

  private buildTaskDistChart(dist: TaskDistribution): Chart {
    return new Chart(this.taskDistCanvas.nativeElement, {
      type: 'doughnut',
      data: {
        labels: ['Por hacer', 'En progreso', 'En revisión', 'Completadas', 'Bloqueadas'],
        datasets: [{
          data: [dist.todo, dist.in_progress, dist.in_review, dist.completed, dist.blocked],
          backgroundColor: ['#9E9E9E', '#2196F3', '#FFC107', '#4CAF50', '#F44336'],
        }],
      },
      options: {
        responsive: false,
        plugins: { legend: { position: 'right' } },
        cutout: '65%',
      },
    });
  }

  private buildResourceChart(data: ResourceUtilization[]): Chart {
    const sorted = [...data].sort((a, b) => b.utilization_percentage - a.utilization_percentage);
    return new Chart(this.resourceCanvas.nativeElement, {
      type: 'bar',
      data: {
        labels: sorted.map(r => r.user_name),
        datasets: [{
          label: 'Utilización (%)',
          data: sorted.map(r => Math.min(r.utilization_percentage, 120)),
          backgroundColor: sorted.map(r =>
            r.utilization_percentage > 90 ? '#F44336' :
            r.utilization_percentage > 70 ? '#FFC107' : '#4CAF50'),
        }],
      },
      options: {
        responsive: false,
        indexAxis: 'y' as const,
        scales: { x: { min: 0, max: 120, title: { display: true, text: 'Utilización (%)' } } },
        plugins: { legend: { display: false } },
      },
    });
  }

  exportExcel(): void {
    this.exportSub?.unsubscribe();
    this.exportSub = this.analyticsService
      .exportExcel({ project_ids: [this.projectId()] })
      .subscribe({
        next: (blob) => {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = `analytics-${this.projectId()}.xlsx`;
          a.click(); URL.revokeObjectURL(url);
          this.toast.success('Excel descargado');
        },
        error: () => this.toast.error('Error al exportar'),
      });
  }
}
