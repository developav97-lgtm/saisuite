import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  effect,
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
import { MatExpansionModule } from '@angular/material/expansion';
import { MatSelectModule } from '@angular/material/select';
import { ReportBIService } from '../../services/report-bi.service';
import { BIFieldConfig, BIFilterV2, BIFilterOperator, BISortConfig } from '../../models/bi-field.model';
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
    MatExpansionModule,
    MatSelectModule,
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

  constructor() {
    // Auto-preview al agregar/quitar campos, cambiar visualización o filtros.
    // El onCleanup cancela el timer anterior si el efecto vuelve a correr antes de los 700 ms.
    effect((onCleanup) => {
      const fields = this.selectedFields();
      const viz    = this.visualization();
      const filts  = this.filters();

      // No ejecutar si no hay nada seleccionado
      if (fields.length === 0 || this.selectedSources().length === 0) return;

      // Suprimir lint: viz y filts se leen solo para registrarlos como dependencias del effect
      void viz; void filts;

      const timer = setTimeout(() => this.preview(), 700);
      onCleanup(() => clearTimeout(timer));
    });
  }

  // ── State ──────────────────────────────────────────────────
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly editMode = signal(false);
  readonly reportId = signal<string | null>(null);

  readonly titulo = signal('');
  readonly selectedSources = signal<string[]>([]);
  readonly selectedFields = signal<BIFieldConfig[]>([]);
  readonly filters = signal<BIFilterV2[]>([]);
  readonly ordenConfig = signal<BISortConfig[]>([]);
  readonly limiteRegistros = signal<number | null>(null);
  readonly visualization = signal<ReportBIVisualization>('table');

  readonly previewResult = signal<ReportBIExecuteResult | null>(null);

  readonly activeFilterCount = computed(() => this.filters().length);

  readonly selectedFieldsForOrder = computed(() =>
    this.selectedFields().map(f => ({ field: f.field, label: f.label, source: f.source })),
  );

  readonly limitOptions: { value: number | null; label: string }[] = [
    { value: null, label: 'Sin límite' },
    { value: 10,   label: 'Top 10' },
    { value: 20,   label: 'Top 20' },
    { value: 50,   label: 'Top 50' },
    { value: 100,  label: 'Top 100' },
    { value: 200,  label: 'Top 200' },
  ];

  readonly vizOptions: { value: ReportBIVisualization; label: string; icon: string }[] = [
    { value: 'table',     label: VISUALIZATION_LABELS['table'],     icon: VISUALIZATION_ICONS['table'] },
    { value: 'pivot',     label: VISUALIZATION_LABELS['pivot'],     icon: VISUALIZATION_ICONS['pivot'] },
    { value: 'bar',       label: VISUALIZATION_LABELS['bar'],       icon: VISUALIZATION_ICONS['bar'] },
    { value: 'line',      label: VISUALIZATION_LABELS['line'],      icon: VISUALIZATION_ICONS['line'] },
    { value: 'pie',       label: VISUALIZATION_LABELS['pie'],       icon: VISUALIZATION_ICONS['pie'] },
    { value: 'area',      label: VISUALIZATION_LABELS['area'],      icon: VISUALIZATION_ICONS['area'] },
    { value: 'kpi',       label: VISUALIZATION_LABELS['kpi'],       icon: VISUALIZATION_ICONS['kpi'] },
    { value: 'waterfall', label: VISUALIZATION_LABELS['waterfall'], icon: VISUALIZATION_ICONS['waterfall'] },
  ];

  readonly canPreview = computed(() =>
    this.selectedSources().length > 0 && this.selectedFields().length > 0,
  );

  readonly canSave = computed(() =>
    this.titulo().trim().length > 0 && this.canPreview(),
  );

  readonly isTable  = computed(() => this.visualization() === 'table');
  readonly isPivot  = computed(() => this.visualization() === 'pivot');
  readonly isChart  = computed(() => {
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

  private readonly pivotVizConfig = computed(() => {
    const fields = this.selectedFields();
    const rows   = fields.filter(f => f.role === 'dimension').map(f => f.field);
    const cols   = fields.filter(f => f.role === 'column').map(f => f.field);
    const values = fields.filter(f => f.role === 'metric').map(f => ({
      field: f.field,
      aggregation: f.is_calculated ? undefined : (f.aggregation ?? 'SUM'),
      is_calculated: f.is_calculated,
      formula: f.formula,
      label: f.label,
    }));
    return { rows, columns: cols, values };
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.reportId.set(id);
      this.editMode.set(true);
      this.loadReport(id);
      return;
    }

    // Fallback: ?template=<id> para templates de BD ya sembrados
    const templateId = this.route.snapshot.queryParamMap.get('template');
    if (templateId) {
      this.loading.set(true);
      this.reportBIService.getById(templateId)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: report => {
            // No heredar el título — el usuario escribirá el suyo
            this.selectedSources.set(report.fuentes);
            this.selectedFields.set(report.campos_config);
            this.filters.set(Array.isArray(report.filtros) ? report.filtros : []);
            if (report.orden_config?.length) this.ordenConfig.set(report.orden_config);
            if (report.limite_registros != null) this.limiteRegistros.set(report.limite_registros);
            this.visualization.set(report.tipo_visualizacion);
            this.loading.set(false);
          },
          error: () => { this.loading.set(false); },
        });
      return;
    }

    // Cargar preset desde query param ?preset= (sugerencias de IA o templates estáticos)
    const presetParam = this.route.snapshot.queryParamMap.get('preset');
    if (presetParam) {
      try {
        const preset = JSON.parse(presetParam) as {
          titulo?: string;
          fuentes?: string[];
          campos_config?: BIFieldConfig[];
          tipo_visualizacion?: ReportBIVisualization;
          filtros?: BIFilterV2[];
          orden_config?: BISortConfig[];
          limite_registros?: number | null;
        };
        if (preset.titulo)                this.titulo.set(preset.titulo);
        if (preset.fuentes?.length)       this.selectedSources.set(preset.fuentes);
        if (preset.campos_config?.length) this.selectedFields.set(preset.campos_config);
        if (preset.tipo_visualizacion)    this.visualization.set(preset.tipo_visualizacion);
        if (Array.isArray(preset.filtros)) {
          this.filters.set(preset.filtros);
        } else if (preset.filtros && typeof preset.filtros === 'object') {
          // Convertir V1 dict → V2 array usando la primera fuente como source
          const src = preset.fuentes?.[0] ?? '';
          const v2 = Object.entries(preset.filtros as Record<string, {op: string; value: unknown}>)
            .map(([field, cond]) => ({
              source: src, field,
              operator: cond.op as BIFilterOperator,
              value: cond.value,
            }));
          this.filters.set(v2);
        }
        if (preset.orden_config?.length) {
          // Solo guardar entradas con campo válido en campos_config
          const validFields = new Set((preset.campos_config ?? []).map(f => f.field));
          const validOrden = preset.orden_config.filter(o => validFields.has(o.field));
          this.ordenConfig.set(validOrden);
        }
        if (preset.limite_registros != null)    this.limiteRegistros.set(preset.limite_registros);
      } catch {
        // JSON inválido → ignorar preset
      }
    }
  }

  private loadReport(id: string): void {
    this.loading.set(true);
    this.reportBIService.getById(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: report => {
          this.titulo.set(report.titulo);
          this.selectedSources.set(report.fuentes);
          this.selectedFields.set(report.campos_config);
          // V2: array de filtros. V1 legacy (dict) se descarta — el backend ejecuta correctamente.
          this.filters.set(Array.isArray(report.filtros) ? report.filtros : []);
          if (report.orden_config?.length) this.ordenConfig.set(report.orden_config);
          if (report.limite_registros != null) this.limiteRegistros.set(report.limite_registros);
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
    this.selectedFields.update(fields => fields.filter(f => sources.includes(f.source)));
  }

  onFieldsChange(fields: BIFieldConfig[]): void {
    this.selectedFields.set(fields);
  }

  onFiltersChange(filters: BIFilterV2[]): void {
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
      orden_config: this.ordenConfig(),
      limite_registros: this.limiteRegistros() ?? 30,
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
      fuentes: this.selectedSources(),
      campos_config: this.selectedFields(),
      tipo_visualizacion: viz,
      viz_config: viz === 'pivot' ? this.pivotVizConfig() : undefined,
      filtros: this.filters(),
      orden_config: this.ordenConfig(),
      limite_registros: this.limiteRegistros(),
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

  // ── Ordenamiento ─────────────────────────────────────────────

  addOrden(): void {
    const first = this.selectedFields()[0];
    if (!first) return;
    this.ordenConfig.update(o => [...o, { field: first.field, direction: 'desc' }]);
  }

  updateOrdenField(i: number, field: string): void {
    this.ordenConfig.update(o => o.map((x, idx) => idx === i ? { ...x, field } : x));
  }

  updateOrdenDir(i: number, direction: 'asc' | 'desc'): void {
    this.ordenConfig.update(o => o.map((x, idx) => idx === i ? { ...x, direction } : x));
  }

  removeOrden(i: number): void {
    this.ordenConfig.update(o => o.filter((_, idx) => idx !== i));
  }

  onLimiteChange(value: number | null): void {
    this.limiteRegistros.set(value);
  }
}
