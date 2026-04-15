import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  computed,
  effect,
  inject,
  input,
  signal,
  untracked,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { DashboardService } from '../../services/dashboard.service';
import { DashboardCard, BiFieldConfigItem } from '../../models/dashboard.model';
import { ChartRendererComponent } from '../chart-renderer/chart-renderer.component';
import { ReportBIExecuteResult, ReportBIVisualization } from '../../models/report-bi.model';
import { BIFieldConfig } from '../../models/bi-field.model';

/** Tarjeta de dashboard que renderiza un ReportBI usando el motor BI (filtros 3 capas). */
@Component({
  selector: 'app-bi-report-card',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterModule,
    MatIconModule,
    MatButtonModule,
    MatMenuModule,
    MatTooltipModule,
    MatProgressBarModule,
    ChartRendererComponent,
  ],
  template: `
    <div class="brc-card">
      <div class="brc-header">
        <h3 class="brc-title">{{ cardTitle() }}</h3>
        <div class="brc-actions">
          @if (reportId()) {
            <a
              mat-icon-button
              [routerLink]="['/saidashboard/reportes', reportId()]"
              matTooltip="Ver como reporte completo"
            >
              <mat-icon>open_in_new</mat-icon>
            </a>
          }
          <button mat-icon-button [matMenuTriggerFor]="cardMenu" matTooltip="Opciones">
            <mat-icon>more_vert</mat-icon>
          </button>
          <mat-menu #cardMenu="matMenu">
            <button mat-menu-item (click)="refresh()">
              <mat-icon>refresh</mat-icon> Actualizar
            </button>
            @if (reportId()) {
              <a mat-menu-item [routerLink]="['/saidashboard/reportes', reportId()]">
                <mat-icon>bar_chart</mat-icon> Ver reporte completo
              </a>
            }
          </mat-menu>
        </div>
      </div>

      @if (loading()) {
        <mat-progress-bar mode="indeterminate" class="brc-progress" />
      }

      <div class="brc-body">
        @if (reportNotAvailable()) {
          <div class="brc-unavailable">
            <mat-icon>broken_image</mat-icon>
            <p>Reporte no disponible</p>
            @if (reportId()) {
              <a mat-stroked-button [routerLink]="['/saidashboard/reportes', reportId()]">
                Abrir reporte
              </a>
            }
          </div>
        } @else {
          <app-chart-renderer
            [data]="executeResult()"
            [visualization]="visualization()"
            [fields]="campos()"
            [loading]="loading()"
          />
        }
      </div>
    </div>
  `,
  styles: [`
    .brc-card {
      background: var(--sc-surface-card);
      border: 1px solid var(--sc-surface-border);
      border-radius: var(--sc-radius);
      box-shadow: var(--sc-shadow-sm);
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
    }

    .brc-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.75rem 0.5rem 0 1rem;
      gap: 0.5rem;
      flex-shrink: 0;
    }

    .brc-title {
      font-size: 0.8125rem;
      font-weight: 600;
      color: var(--sc-text-color);
      margin: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      flex: 1;
    }

    .brc-actions {
      display: flex;
      align-items: center;
      flex-shrink: 0;
    }

    .brc-progress {
      margin: 0.25rem 0 -4px;
      flex-shrink: 0;
    }

    .brc-body {
      flex: 1;
      min-height: 0;
      overflow: hidden;
    }

    .brc-unavailable {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      min-height: 120px;
      gap: 0.5rem;
      color: var(--sc-text-muted);

      mat-icon {
        font-size: 2rem;
        width: 2rem;
        height: 2rem;
        opacity: 0.3;
      }

      p {
        font-size: 0.8125rem;
        margin: 0;
      }
    }
  `],
})
export class BiReportCardComponent {
  readonly card = input.required<DashboardCard>();
  readonly dashboardId = input.required<string>();
  readonly dashboardFilters = input<Record<string, unknown>>({});

  private readonly dashboardService = inject(DashboardService);
  private readonly destroyRef = inject(DestroyRef);

  readonly loading = signal(true);
  readonly executeResult = signal<ReportBIExecuteResult | null>(null);
  readonly reportNotAvailable = signal(false);

  readonly cardTitle = computed(
    () => this.card().titulo_personalizado || this.card().bi_report_titulo || 'Reporte BI',
  );
  readonly reportId = computed(() => this.card().bi_report_id);
  readonly visualization = computed(
    () => (this.card().bi_report_tipo_visualizacion as ReportBIVisualization | null) ?? 'bar',
  );
  readonly campos = computed((): BIFieldConfig[] => {
    const raw = this.card().bi_report_campos_config as BiFieldConfigItem[] | null;
    if (!raw) return [];
    return raw.map(c => ({
      source: c.source,
      field: c.field,
      role: c.role,
      label: c.label,
      aggregation: c.aggregation,
      formula: c.formula,
      is_calculated: c.is_calculated,
    } as BIFieldConfig));
  });

  constructor() {
    // Re-executes when card or dashboardFilters inputs change (reactive to filter changes).
    effect(() => {
      const card = this.card();
      const filters = this.dashboardFilters();
      const dashId = this.dashboardId();
      untracked(() => this.executeLoad(card, filters, dashId));
    });
  }

  refresh(): void {
    this.executeLoad(this.card(), this.dashboardFilters(), this.dashboardId());
  }

  private executeLoad(c: DashboardCard, filters: Record<string, unknown>, dashId: string): void {
    if (!c.bi_report_id) {
      this.reportNotAvailable.set(true);
      this.loading.set(false);
      return;
    }

    this.loading.set(true);
    this.reportNotAvailable.set(false);

    this.dashboardService
      .executeBiCard(dashId, c.id, filters)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (result) => {
          this.executeResult.set(result as ReportBIExecuteResult);
          this.loading.set(false);
        },
        error: () => {
          this.reportNotAvailable.set(true);
          this.loading.set(false);
        },
      });
  }
}
