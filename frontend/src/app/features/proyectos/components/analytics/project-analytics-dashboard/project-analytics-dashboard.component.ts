import {
  Component,
  OnInit,
  OnDestroy,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
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
import { MatSnackBar } from '@angular/material/snack-bar';
import { Chart } from 'chart.js';
import { AnalyticsService } from '../../../services/analytics.service';
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
export class ProjectAnalyticsDashboardComponent implements OnInit, OnDestroy {
  private readonly analyticsService = inject(AnalyticsService);
  private readonly snackBar = inject(MatSnackBar);
  private readonly cdr = inject(ChangeDetectorRef);

  readonly projectId = input.required<string>();

  // State signals
  readonly loading = signal(false);
  readonly kpis = signal<ProjectKPIs | null>(null);
  readonly taskDistribution = signal<TaskDistribution | null>(null);
  readonly velocityData = signal<VelocityDataPoint[]>([]);
  readonly burnDownData = signal<BurnDownData | null>(null);
  readonly resourceUtilization = signal<ResourceUtilization[]>([]);

  // Chart canvas refs
  @ViewChild('burnDownCanvas') burnDownCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('velocityCanvas') velocityCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('taskDistCanvas') taskDistCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('resourceCanvas') resourceCanvas!: ElementRef<HTMLCanvasElement>;

  // Computed signals for KPI display state
  readonly completionClass  = computed(() => this.kpiClass(this.kpis()?.completion_rate ?? 0));
  readonly onTimeClass      = computed(() => this.kpiClass(this.kpis()?.on_time_rate ?? 0));
  readonly budgetClass_     = computed(() => this.budgetClass(this.kpis()?.budget_variance ?? null));
  readonly budgetVarianceFmt = computed(() => this.formatVariance(this.kpis()?.budget_variance ?? null));

  private charts: Chart[] = [];
  private loadSub: Subscription | null = null;
  private exportSub: Subscription | null = null;

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.destroyCharts();
    this.loadSub?.unsubscribe();
    this.exportSub?.unsubscribe();
  }

  loadData(): void {
    this.loadSub?.unsubscribe();
    this.loading.set(true);
    const id = this.projectId();

    this.loadSub = forkJoin({
      kpis: this.analyticsService.getKPIs(id),
      distribution: this.analyticsService.getTaskDistribution(id),
      velocity: this.analyticsService.getVelocity(id),
      burnDown: this.analyticsService.getBurnDown(id),
      resources: this.analyticsService.getResourceUtilization(id),
    }).subscribe({
      next: (data) => {
        this.kpis.set(data.kpis);
        this.taskDistribution.set(data.distribution);
        // Backend wraps velocity in { periods, data: [...] }
        this.velocityData.set(data.velocity.data);
        this.burnDownData.set(data.burnDown);
        this.resourceUtilization.set(data.resources);
        this.loading.set(false);
        this.cdr.detectChanges();
        // Build charts after data arrives — use setTimeout to let template render
        setTimeout(() => this.buildCharts(), 0);
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error al cargar analytics', 'Cerrar', {
          duration: 4000,
          panelClass: ['snack-error'],
        });
      },
    });
  }

  // ── KPI helpers ──────────────────────────────────────────────────

  kpiClass(value: number): string {
    if (value >= 75) return 'pad-kpi__trend--up';
    if (value >= 50) return 'pad-kpi__trend--warn';
    return 'pad-kpi__trend--danger';
  }

  budgetClass(variance: number | null): string {
    if (variance === null) return 'pad-kpi__trend--neutral';
    // Negative = under budget (good); Positive = over budget (bad)
    if (variance <= 0) return 'pad-kpi__trend--up';
    if (variance <= 10) return 'pad-kpi__trend--warn';
    return 'pad-kpi__trend--danger';
  }

  formatVariance(v: number | null): string {
    if (v === null) return 'N/A';
    return v >= 0 ? `+${v.toFixed(1)}%` : `${v.toFixed(1)}%`;
  }

  // ── Charts ───────────────────────────────────────────────────────

  private destroyCharts(): void {
    this.charts.forEach(c => c.destroy());
    this.charts = [];
  }

  private buildCharts(): void {
    this.destroyCharts();
    const burnDown = this.burnDownData();
    const velocity = this.velocityData();
    const dist = this.taskDistribution();
    const resources = this.resourceUtilization();

    if (this.burnDownCanvas?.nativeElement && burnDown) {
      this.charts.push(this.buildBurnDownChart(burnDown));
    }
    if (this.velocityCanvas?.nativeElement && velocity.length) {
      this.charts.push(this.buildVelocityChart(velocity));
    }
    if (this.taskDistCanvas?.nativeElement && dist) {
      this.charts.push(this.buildTaskDistChart(dist));
    }
    if (this.resourceCanvas?.nativeElement && resources.length) {
      this.charts.push(this.buildResourceChart(resources));
    }
  }

  private buildBurnDownChart(data: BurnDownData): Chart {
    const labels = data.data_points.map(p => p.week_label);
    return new Chart(this.burnDownCanvas.nativeElement, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Ideal',
            data: data.data_points.map(p => p.hours_ideal),
            borderColor: '#9E9E9E',
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false,
          },
          {
            label: 'Estimadas restantes',
            data: data.data_points.map(p => p.hours_remaining),
            borderColor: '#1976d2',
            backgroundColor: 'rgba(25,118,210,0.08)',
            fill: true,
            tension: 0.3,
          },
          {
            label: 'Acumuladas reales',
            data: data.data_points.map(p => p.hours_actual_cumulative),
            borderColor: '#4CAF50',
            fill: false,
            tension: 0.3,
          },
        ],
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Horas' },
          },
        },
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
          {
            label: 'Tareas completadas',
            data: data.map(p => p.tasks_completed),
            backgroundColor: data.map(p =>
              p.tasks_completed >= avg ? '#4CAF50' : '#F44336'
            ),
          },
          {
            label: 'Media',
            data: data.map(() => avg),
            type: 'line' as const,
            borderColor: '#FFC107',
            borderDash: [4, 4],
            pointRadius: 0,
            fill: false,
          },
        ],
      },
      options: {
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
        datasets: [
          {
            data: [
              dist.todo,
              dist.in_progress,
              dist.in_review,
              dist.completed,
              dist.blocked,
            ],
            backgroundColor: ['#9E9E9E', '#2196F3', '#FFC107', '#4CAF50', '#F44336'],
          },
        ],
      },
      options: {
        plugins: { legend: { position: 'right' } },
        cutout: '65%',
      },
    });
  }

  private buildResourceChart(data: ResourceUtilization[]): Chart {
    const sorted = [...data].sort(
      (a, b) => b.utilization_percentage - a.utilization_percentage
    );
    return new Chart(this.resourceCanvas.nativeElement, {
      type: 'bar',
      data: {
        labels: sorted.map(r => r.user_name),
        datasets: [
          {
            label: 'Utilización (%)',
            data: sorted.map(r => Math.min(r.utilization_percentage, 120)),
            backgroundColor: sorted.map(r => {
              if (r.utilization_percentage > 90) return '#F44336';
              if (r.utilization_percentage > 70) return '#FFC107';
              return '#4CAF50';
            }),
          },
        ],
      },
      options: {
        indexAxis: 'y' as const,
        scales: {
          x: {
            min: 0,
            max: 120,
            title: { display: true, text: 'Utilización (%)' },
          },
        },
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
          a.href = url;
          a.download = `analytics-${this.projectId()}.xlsx`;
          a.click();
          URL.revokeObjectURL(url);
          this.snackBar.open('Excel descargado', 'Cerrar', {
            duration: 3000,
            panelClass: ['snack-success'],
          });
        },
        error: () =>
          this.snackBar.open('Error al exportar', 'Cerrar', {
            duration: 4000,
            panelClass: ['snack-error'],
          }),
      });
  }
}
