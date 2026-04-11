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
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ReportBIService } from '../../services/report-bi.service';
import { BIFieldConfig } from '../../models/bi-field.model';
import {
  ReportBICreateRequest,
  ReportBIExecuteResult,
  ReportBIVisualization,
  isPivotResult,
  isTableResult,
  VISUALIZATION_ICONS,
  VISUALIZATION_LABELS,
} from '../../models/report-bi.model';
import { SourceSelectorComponent } from '../source-selector/source-selector.component';
import { FieldPanelComponent } from '../field-panel/field-panel.component';
import { FilterBuilderComponent } from '../filter-builder/filter-builder.component';
import { DataTableComponent } from '../data-table/data-table.component';
import { PivotTableComponent } from '../pivot-table/pivot-table.component';
import { ChartRendererComponent } from '../chart-renderer/chart-renderer.component';
import { ExportMenuComponent } from '../export-menu/export-menu.component';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-report-builder',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatProgressBarModule,
    MatButtonToggleModule,
    MatTooltipModule,
    SourceSelectorComponent,
    FieldPanelComponent,
    FilterBuilderComponent,
    DataTableComponent,
    PivotTableComponent,
    ChartRendererComponent,
    ExportMenuComponent,
  ],
  templateUrl: './report-builder.component.html',
  styleUrl: './report-builder.component.scss',
})
export class ReportBuilderComponent implements OnInit {
  private readonly reportBIService = inject(ReportBIService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  // ── State ──────────────────────────────────────────────────
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly editMode = signal(false);
  readonly reportId = signal<string | null>(null);

  readonly titulo = signal('');
  readonly descripcion = signal('');
  readonly selectedSources = signal<string[]>([]);
  readonly selectedFields = signal<BIFieldConfig[]>([]);
  readonly filters = signal<Record<string, unknown>>({});
  readonly visualization = signal<ReportBIVisualization>('table');

  readonly previewResult = signal<ReportBIExecuteResult | null>(null);

  readonly vizOptions: { value: ReportBIVisualization; label: string; icon: string }[] = [
    { value: 'table', label: VISUALIZATION_LABELS['table'], icon: VISUALIZATION_ICONS['table'] },
    { value: 'pivot', label: VISUALIZATION_LABELS['pivot'], icon: VISUALIZATION_ICONS['pivot'] },
    { value: 'bar',   label: VISUALIZATION_LABELS['bar'],   icon: VISUALIZATION_ICONS['bar'] },
    { value: 'line',  label: VISUALIZATION_LABELS['line'],  icon: VISUALIZATION_ICONS['line'] },
    { value: 'pie',   label: VISUALIZATION_LABELS['pie'],   icon: VISUALIZATION_ICONS['pie'] },
    { value: 'area',  label: VISUALIZATION_LABELS['area'],  icon: VISUALIZATION_ICONS['area'] },
    { value: 'kpi',   label: VISUALIZATION_LABELS['kpi'],   icon: VISUALIZATION_ICONS['kpi'] },
    { value: 'waterfall', label: VISUALIZATION_LABELS['waterfall'], icon: VISUALIZATION_ICONS['waterfall'] },
  ];

  readonly canPreview = computed(() =>
    this.selectedSources().length > 0 && this.selectedFields().length > 0,
  );

  readonly canSave = computed(() =>
    this.titulo().trim().length > 0 && this.canPreview(),
  );

  readonly isTable = computed(() => this.visualization() === 'table');
  readonly isPivot = computed(() => this.visualization() === 'pivot');
  readonly isChart = computed(() => {
    const v = this.visualization();
    return v !== 'table' && v !== 'pivot';
  });

  readonly tableResult = computed(() => {
    const r = this.previewResult();
    return r && isTableResult(r) ? r : null;
  });

  readonly pivotResult = computed(() => {
    const r = this.previewResult();
    return r && isPivotResult(r) ? r : null;
  });

  /** Build viz_config for pivot from selected fields */
  private readonly pivotVizConfig = computed(() => {
    const fields = this.selectedFields();
    const rows = fields.filter(f => f.role === 'dimension').map(f => f.field);
    const cols = fields.filter(f => f.role === 'column').map(f => f.field);
    const values = fields.filter(f => f.role === 'metric').map(f => ({
      field: f.field,
      aggregation: f.aggregation ?? 'SUM',
    }));
    return { rows, columns: cols, values };
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.reportId.set(id);
      this.editMode.set(true);
      this.loadReport(id);
    }
  }

  private loadReport(id: string): void {
    this.loading.set(true);
    this.reportBIService.getById(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: report => {
          this.titulo.set(report.titulo);
          this.descripcion.set(report.descripcion);
          this.selectedSources.set(report.fuentes);
          this.selectedFields.set(report.campos_config);
          this.filters.set(report.filtros);
          this.visualization.set(report.tipo_visualizacion);
          this.loading.set(false);
        },
        error: () => {
          this.toast.error('Error al cargar el reporte.');
          this.loading.set(false);
        },
      });
  }

  // ── Handlers ────────────────────────────────────────────────

  onSourcesChange(sources: string[]): void {
    this.selectedSources.set(sources);
    this.selectedFields.update(fields =>
      fields.filter(f => sources.includes(f.source)),
    );
  }

  onFieldsChange(fields: BIFieldConfig[]): void {
    this.selectedFields.set(fields);
  }

  onFiltersChange(filters: Record<string, unknown>): void {
    this.filters.set(filters);
  }

  onVisualizationChange(viz: ReportBIVisualization): void {
    this.visualization.set(viz);
  }

  // ── Actions ────────────────────────────────────────────────

  preview(): void {
    if (!this.canPreview()) return;

    this.loading.set(true);
    const viz = this.visualization();
    this.reportBIService.preview({
      fuentes: this.selectedSources(),
      campos_config: this.selectedFields(),
      tipo_visualizacion: viz,
      viz_config: viz === 'pivot' ? this.pivotVizConfig() : undefined,
      filtros: this.filters(),
    })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: result => {
          this.previewResult.set(result);
          this.loading.set(false);
        },
        error: () => {
          this.toast.error('Error al ejecutar la consulta.');
          this.loading.set(false);
        },
      });
  }

  save(): void {
    if (!this.canSave()) return;

    this.saving.set(true);
    const viz = this.visualization();
    const data: ReportBICreateRequest = {
      titulo: this.titulo(),
      descripcion: this.descripcion(),
      fuentes: this.selectedSources(),
      campos_config: this.selectedFields(),
      tipo_visualizacion: viz,
      viz_config: viz === 'pivot' ? this.pivotVizConfig() : undefined,
      filtros: this.filters(),
    };

    const obs = this.editMode()
      ? this.reportBIService.update(this.reportId()!, data)
      : this.reportBIService.create(data);

    obs.pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: report => {
          this.saving.set(false);
          this.toast.success(this.editMode() ? 'Reporte actualizado.' : 'Reporte creado.');
          this.router.navigate(['/saidashboard', 'reportes', report.id]);
        },
        error: () => {
          this.saving.set(false);
          this.toast.error('Error al guardar el reporte.');
        },
      });
  }

  goBack(): void {
    this.router.navigate(['/saidashboard', 'reportes']);
  }
}
