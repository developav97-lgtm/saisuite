import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  OnInit,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialog } from '@angular/material/dialog';
import { forkJoin } from 'rxjs';
import { NavigationHistoryService } from '../../../../core/services/navigation-history.service';
import { DashboardService } from '../../services/dashboard.service';
import { ReportService } from '../../services/report.service';
import { TrialService } from '../../services/trial.service';
import {
  DashboardDetail,
  DashboardCard,
} from '../../models/dashboard.model';
import { CardDataResponse, ReportFilter } from '../../models/report-filter.model';
import { TrialStatus } from '../../models/trial.model';
import { ModuleTrialStatus } from '../../../admin/models/tenant.model';
import { ChartCardComponent } from '../chart-card/chart-card.component';
import { KpiCardComponent } from '../kpi-card/kpi-card.component';
import { BiReportCardComponent } from '../bi-report-card/bi-report-card.component';
import { FilterPanelComponent } from '../filter-panel/filter-panel.component';
import { TrialBannerComponent } from '../../../../shared/components/trial-banner/trial-banner.component';
import { ShareDialogComponent, ShareDialogData } from '../share-dialog/share-dialog.component';
import { ToastService } from '../../../../core/services/toast.service';
import { ChatStateService } from '../../../../core/services/chat-state.service';

interface CardWithData {
  card: DashboardCard;
  data: CardDataResponse | null;
  loading: boolean;
}

@Component({
  selector: 'app-dashboard-viewer',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatTooltipModule,
    MatProgressBarModule,
    ChartCardComponent,
    KpiCardComponent,
    BiReportCardComponent,
    FilterPanelComponent,
    TrialBannerComponent,
  ],
  templateUrl: './dashboard-viewer.component.html',
  styleUrl: './dashboard-viewer.component.scss',
})
export class DashboardViewerComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly dashboardService = inject(DashboardService);
  private readonly reportService = inject(ReportService);
  private readonly trialService = inject(TrialService);
  private readonly dialog = inject(MatDialog);
  private readonly toast = inject(ToastService);
  private readonly chatState = inject(ChatStateService);
  private readonly navHistory = inject(NavigationHistoryService);
  private readonly destroyRef = inject(DestroyRef);

  readonly dashboardContent = viewChild<ElementRef<HTMLElement>>('dashboardContent');

  // ── State ──────────────────────────────────────────────────
  readonly loading = signal(true);
  readonly dashboard = signal<DashboardDetail | null>(null);
  readonly cardsWithData = signal<CardWithData[]>([]);
  readonly trialStatus = signal<TrialStatus | null>(null);
  readonly showFilters = signal(false);

  /** Mapea TrialStatus → ModuleTrialStatus para el banner compartido */
  readonly trialStatusMapped = computed<ModuleTrialStatus | null>(() => {
    const s = this.trialStatus();
    if (!s) return null;
    return {
      tiene_acceso: s.tiene_acceso,
      tipo_acceso:  s.tipo_acceso === 'licensed' ? 'license' : s.tipo_acceso,
      trial_activo: s.tipo_acceso === 'trial',
      trial_usado:  false,
      dias_restantes: s.dias_restantes,
      expira_en:    s.expira_en,
    } satisfies ModuleTrialStatus;
  });
  readonly exporting = signal(false);

  readonly currentFilter = signal<ReportFilter>({
    fecha_desde: null,
    fecha_hasta: null,
  });

  // ── Computed ───────────────────────────────────────────────
  readonly title = computed(() => this.dashboard()?.titulo ?? 'Dashboard');
  readonly isFavorite = computed(() => this.dashboard()?.es_favorito ?? false);

  /** Tarjetas BI (tipo bi_report) — cargan sus propios datos vía BiReportCardComponent. */
  readonly biReportCards = computed(() =>
    this.dashboard()?.cards.filter(c => c.card_type_code === 'bi_report') ?? [],
  );

  /** Filtros del dashboard actuales como Record para pasar a BiReportCardComponent. */
  readonly dashboardFiltersMap = computed((): Record<string, unknown> => {
    const f = this.currentFilter();
    const result: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(f)) {
      if (v !== null && v !== undefined) {
        result[k] = v;
      }
    }
    return result;
  });

  readonly kpiCards = computed(() =>
    this.cardsWithData().filter(c =>
      c.card.chart_type === 'kpi' && !c.card.filtros_config['agrupar_por_mes'],
    ),
  );

  readonly chartCards = computed(() =>
    this.cardsWithData().filter(c =>
      c.card.chart_type !== 'kpi' || !!c.card.filtros_config['agrupar_por_mes'],
    ),
  );

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      this.router.navigate(['/saidashboard']);
      return;
    }
    this.loadDashboard(id);
    this.loadTrialStatus();
  }

  private loadDashboard(id: string): void {
    this.loading.set(true);
    this.dashboardService.getById(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: detail => {
          this.dashboard.set(detail);
          this.loading.set(false);

          // Inicializar filtros desde filtros_default del dashboard
          if (detail.filtros_default) {
            this.currentFilter.set(detail.filtros_default);
          }

          this.loadAllCardData(detail.cards);
        },
        error: () => {
          this.toast.error('Error al cargar el dashboard.');
          this.loading.set(false);
          this.router.navigate(['/saidashboard']);
        },
      });
  }

  private loadTrialStatus(): void {
    this.trialService.getStatus()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: status => this.trialStatus.set(status),
      });
  }

  private loadAllCardData(cards: DashboardCard[]): void {
    // bi_report cards manage their own data loading via BiReportCardComponent
    const regularCards = cards.filter(c => c.card_type_code !== 'bi_report');

    // Initialize regular cards with loading state
    const initial: CardWithData[] = regularCards.map(card => ({
      card,
      data: null,
      loading: true,
    }));
    this.cardsWithData.set(initial);

    if (regularCards.length === 0) return;

    const filter = this.currentFilter();
    const requests = regularCards.map(card =>
      this.reportService.getCardData({
        card_type_code: card.card_type_code,
        filtros: filter,
        card_config: card.filtros_config,
      }),
    );

    forkJoin(requests)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: responses => {
          const updated: CardWithData[] = regularCards.map((card, i) => ({
            card,
            data: responses[i],
            loading: false,
          }));
          this.cardsWithData.set(updated);
        },
        error: () => {
          this.cardsWithData.update(list =>
            list.map(c => ({ ...c, loading: false })),
          );
          this.toast.error('Error al cargar datos de las tarjetas.');
        },
      });
  }

  // ── Actions ────────────────────────────────────────────────
  onFilterChange(filter: ReportFilter): void {
    this.currentFilter.set(filter);
    const cards = this.dashboard()?.cards;
    if (cards) {
      this.loadAllCardData(cards);
    }
  }

  onSaveAsDefault(filter: ReportFilter): void {
    const d = this.dashboard();
    if (!d) return;

    this.dashboardService.saveDefaultFilters(d.id, filter)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: updated => {
          this.dashboard.set(updated);
          this.toast.success('Filtros guardados como predeterminados.');
        },
        error: () => this.toast.error('Error al guardar filtros predeterminados.'),
      });
  }

  toggleFilters(): void {
    this.showFilters.update(v => !v);
  }

  openCfoVirtual(): void {
    this.chatState.openBot('dashboard');
  }

  toggleFavorite(): void {
    const d = this.dashboard();
    if (!d) return;

    this.dashboardService.toggleFavorite(d.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.dashboard.update(db =>
            db ? { ...db, es_favorito: res.es_favorito } : db,
          );
          this.toast.success(
            res.es_favorito ? 'Agregado a favoritos.' : 'Removido de favoritos.',
          );
        },
        error: () => this.toast.error('Error al cambiar favorito.'),
      });
  }

  editDashboard(): void {
    const d = this.dashboard();
    if (d) {
      this.router.navigate(['/saidashboard', 'builder', d.id]);
    }
  }

  openShareDialog(): void {
    const d = this.dashboard();
    if (!d) return;

    this.dialog.open(ShareDialogComponent, {
      width: '560px',
      maxWidth: '95vw',
      data: {
        dashboardId: d.id,
        dashboardTitle: d.titulo,
        currentShares: d.shares,
      } as ShareDialogData,
    });
  }

  async exportPDF(): Promise<void> {
    const content = this.dashboardContent()?.nativeElement;
    if (!content) return;

    this.exporting.set(true);
    try {
      await this.reportService.exportToPDF(content, this.title());
      this.toast.success('PDF exportado correctamente.');
    } catch {
      this.toast.error('Error al exportar PDF.');
    } finally {
      this.exporting.set(false);
    }
  }

  goBack(): void {
    this.navHistory.goBack('/saidashboard');
  }

  getCardTitle(cwd: CardWithData): string {
    return cwd.card.titulo_personalizado || cwd.card.card_type_code;
  }

  getSummaryValue(cwd: CardWithData, key: string): number {
    const val = cwd.data?.summary?.[key];
    return typeof val === 'number' ? val : 0;
  }

  getSummaryPrevious(cwd: CardWithData, key: string): number | null {
    const val = cwd.data?.summary?.[`${key}_anterior`];
    return typeof val === 'number' ? val : null;
  }
}
