import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog } from '@angular/material/dialog';
import { AuthService } from '../../../../core/auth/auth.service';
import { ReportBIService } from '../../services/report-bi.service';
import { ReportShareDialogComponent, ReportShareDialogData } from '../report-share-dialog/report-share-dialog.component';
import {
  ReportBIDetail,
  ReportBIExecuteResult,
  isPivotResult,
  isTableResult,
  VISUALIZATION_LABELS,
  VISUALIZATION_ICONS,
} from '../../models/report-bi.model';
import { DataTableComponent } from '../data-table/data-table.component';
import { PivotTableComponent, PivotCellClick } from '../pivot-table/pivot-table.component';
import { ChartRendererComponent } from '../chart-renderer/chart-renderer.component';
import { DrillDownPanelComponent, DrillDownData } from '../drill-down-panel/drill-down-panel.component';
import { ExportMenuComponent } from '../export-menu/export-menu.component';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-report-viewer',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatChipsModule,
    DataTableComponent,
    PivotTableComponent,
    ChartRendererComponent,
    DrillDownPanelComponent,
    ExportMenuComponent,
  ],
  templateUrl: './report-viewer.component.html',
  styleUrl: './report-viewer.component.scss',
})
export class ReportViewerComponent implements OnInit {
  private readonly reportService = inject(ReportBIService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);
  private readonly dialog = inject(MatDialog);
  private readonly auth = inject(AuthService);
  private readonly destroyRef = inject(DestroyRef);

  readonly loading = signal(true);
  readonly executing = signal(false);
  readonly report = signal<ReportBIDetail | null>(null);
  readonly result = signal<ReportBIExecuteResult | null>(null);
  readonly drillDown = signal<DrillDownData | null>(null);

  readonly vizLabel = computed(() => {
    const r = this.report();
    return r ? VISUALIZATION_LABELS[r.tipo_visualizacion] : '';
  });

  readonly vizIcon = computed(() => {
    const r = this.report();
    return r ? VISUALIZATION_ICONS[r.tipo_visualizacion] : '';
  });

  readonly isTable = computed(() => this.report()?.tipo_visualizacion === 'table');
  readonly isPivot = computed(() => this.report()?.tipo_visualizacion === 'pivot');
  readonly isChart = computed(() => {
    const viz = this.report()?.tipo_visualizacion;
    return viz !== undefined && viz !== 'table' && viz !== 'pivot';
  });

  readonly tableResult = computed(() => {
    const r = this.result();
    return r && isTableResult(r) ? r : null;
  });

  readonly pivotResult = computed(() => {
    const r = this.result();
    return r && isPivotResult(r) ? r : null;
  });

  readonly sourceLabels = computed(() => {
    const r = this.report();
    return r?.fuentes ?? [];
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      this.router.navigate(['/saidashboard', 'reportes']);
      return;
    }
    this.loadAndExecute(id);
  }

  private loadAndExecute(id: string): void {
    this.loading.set(true);
    this.reportService.getById(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: report => {
          this.report.set(report);
          this.loading.set(false);
          this.execute(id);
        },
        error: () => {
          this.toast.error('Error al cargar el reporte.');
          this.loading.set(false);
        },
      });
  }

  execute(id?: string): void {
    const reportId = id ?? this.report()?.id;
    if (!reportId) return;
    this.executing.set(true);
    this.reportService.execute(reportId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: result => {
          this.result.set(result);
          this.executing.set(false);
        },
        error: () => {
          this.toast.error('Error al ejecutar el reporte.');
          this.executing.set(false);
        },
      });
  }

  toggleFavorite(): void {
    const r = this.report();
    if (!r) return;
    this.reportService.toggleFavorite(r.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.report.update(rpt => rpt ? { ...rpt, es_favorito: res.es_favorito } : rpt);
        },
      });
  }

  goBack(): void {
    this.router.navigate(['/saidashboard', 'reportes']);
  }

  goEdit(): void {
    const r = this.report();
    if (r) this.router.navigate(['/saidashboard', 'reportes', r.id, 'edit']);
  }

  onPivotCellClick(event: PivotCellClick): void {
    this.drillDown.set({
      title: `Detalle: ${Object.values(event.rowHeaders).join(' / ')} × ${Object.values(event.colHeaders).join(' / ')}`,
      filters: { ...event.rowHeaders, ...event.colHeaders },
      columns: [],
      rows: [],
      loading: true,
    });

    // Execute a preview with the pivot cell filters to get detail rows
    const r = this.report();
    if (!r) return;
    const drillFilters = { ...r.filtros, ...event.rowHeaders, ...event.colHeaders };
    this.reportService.preview({
      fuentes: r.fuentes,
      campos_config: r.campos_config,
      tipo_visualizacion: 'table',
      filtros: drillFilters,
      limite_registros: 100,
    }).pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          if (isTableResult(res)) {
            this.drillDown.set({
              title: `Detalle: ${Object.values(event.rowHeaders).join(' / ')} × ${Object.values(event.colHeaders).join(' / ')}`,
              filters: { ...event.rowHeaders, ...event.colHeaders },
              columns: res.columns.map(c => c.field),
              rows: res.rows,
              loading: false,
            });
          }
        },
        error: () => {
          this.drillDown.set(null);
          this.toast.error('Error al cargar detalle.');
        },
      });
  }

  onTableCellClick(event: { row: Record<string, unknown>; column: string }): void {
    this.drillDown.set({
      title: `Detalle: ${event.column} = ${String(event.row[event.column] ?? '')}`,
      filters: { [event.column]: event.row[event.column] },
      columns: Object.keys(event.row),
      rows: [event.row],
      loading: false,
    });
  }

  onChartClick(event: { label: string; datasetIndex: number; index: number }): void {
    const r = this.report();
    if (!r) return;
    const dims = r.campos_config.filter(f => f.role === 'dimension');
    if (dims.length === 0) return;
    const filterField = dims[0].field;

    this.drillDown.set({
      title: `Detalle: ${event.label}`,
      filters: { [filterField]: event.label },
      columns: [],
      rows: [],
      loading: true,
    });

    this.reportService.preview({
      fuentes: r.fuentes,
      campos_config: r.campos_config,
      tipo_visualizacion: 'table',
      filtros: { ...r.filtros, [filterField]: event.label },
      limite_registros: 100,
    }).pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          if (isTableResult(res)) {
            this.drillDown.set({
              title: `Detalle: ${event.label}`,
              filters: { [filterField]: event.label },
              columns: res.columns.map(c => c.field),
              rows: res.rows,
              loading: false,
            });
          }
        },
        error: () => {
          this.drillDown.set(null);
          this.toast.error('Error al cargar detalle.');
        },
      });
  }

  openShareDialog(): void {
    const r = this.report();
    if (!r) return;

    this.dialog.open(ReportShareDialogComponent, {
      width: '520px',
      data: {
        reportId: r.id,
        reportTitle: r.titulo,
        existingShares: r.shares ?? [],
        currentUserId: this.auth.currentUser()?.id ?? '',
      } satisfies ReportShareDialogData,
    });
  }

  closeDrillDown(): void {
    this.drillDown.set(null);
  }
}
