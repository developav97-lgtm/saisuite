import { ChangeDetectionStrategy, Component, OnInit, inject, signal, computed } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatTabsModule } from '@angular/material/tabs';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog } from '@angular/material/dialog';
import { ProyectoService } from '../../services/proyecto.service';
import { ProyectoDetail, EstadoProyecto, ESTADO_LABELS, ESTADO_SEVERITY, TIPO_LABELS } from '../../models/proyecto.model';
import { FaseListComponent } from '../fase-list/fase-list.component';
import { TerceroListComponent } from '../tercero-list/tercero-list.component';
import { DocumentoListComponent } from '../documento-list/documento-list.component';
import { HitoListComponent } from '../hito-list/hito-list.component';
import { ActividadProyectoListComponent } from '../actividad-proyecto-list/actividad-proyecto-list.component';
import { GanttViewComponent } from '../gantt-view/gantt-view.component';
import { TeamTimelineComponent } from '../team-timeline/team-timeline.component';
import { ProjectAnalyticsDashboardComponent } from '../analytics/project-analytics-dashboard/project-analytics-dashboard.component';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { AutoScheduleDialogComponent } from '../scheduling/auto-schedule-dialog/auto-schedule-dialog.component';
import { BaselineComparisonComponent } from '../scheduling/baseline-comparison/baseline-comparison.component';
import { WhatIfScenarioBuilderComponent } from '../scheduling/what-if-scenario-builder/what-if-scenario-builder.component';
import { BudgetDashboardComponent } from '../budget-dashboard/budget-dashboard.component';
import { TareaListComponent } from '../tarea-list/tarea-list.component';
import { TareaKanbanComponent } from '../tarea-kanban/tarea-kanban.component';
import { ProyectoTimesheetTabComponent } from './proyecto-timesheet-tab/proyecto-timesheet-tab.component';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-proyecto-detail',
  templateUrl: './proyecto-detail.component.html',
  styleUrl: './proyecto-detail.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    RouterLink,
    MatTabsModule, MatButtonModule, MatIconModule, MatProgressBarModule,
    FaseListComponent,
    TerceroListComponent,
    DocumentoListComponent,
    HitoListComponent,
    ActividadProyectoListComponent,
    GanttViewComponent,
    TeamTimelineComponent,
    ProjectAnalyticsDashboardComponent,
    MatMenuModule,
    MatTooltipModule,
    BaselineComparisonComponent,
    WhatIfScenarioBuilderComponent,
    BudgetDashboardComponent,
    TareaListComponent,
    TareaKanbanComponent,
    ProyectoTimesheetTabComponent,
  ],
})
export class ProyectoDetailComponent implements OnInit {
  private readonly route           = inject(ActivatedRoute);
  private readonly router          = inject(Router);
  private readonly proyectoService = inject(ProyectoService);
  private readonly dialog          = inject(MatDialog);
  private readonly toast       = inject(ToastService);

  readonly proyecto = signal<ProyectoDetail | null>(null);
  readonly loading  = signal(true);
  readonly selectedTab = signal(0);
  // Tab indices:
  // General(0) Fases(1) Terceros(2) Docs(3) Hitos(4) Tareas(5) Kanban(6)
  // Actividades(7) Gantt(8) Equipo(9) Timesheets(10)
  // Analytics(11) Baselines(12) Escenarios(13) Presupuesto(14)
  readonly tareasTabLoaded       = computed(() => this.selectedTab() >= 5);
  readonly kanbanTabLoaded       = computed(() => this.selectedTab() >= 6);
  readonly timesheetsTabLoaded   = computed(() => this.selectedTab() >= 10);
  readonly analyticsTabActive    = computed(() => this.selectedTab() === 11);
  readonly baselinesTabLoaded    = computed(() => this.selectedTab() >= 12);
  readonly escenariosTabLoaded   = computed(() => this.selectedTab() >= 13);
  readonly presupuestoTabLoaded  = computed(() => this.selectedTab() >= 14);

  readonly actividadesTabLabel = computed(() =>
    this.proyecto()?.tipo === 'civil_works' ? 'Actividades de obra' : 'Actividades'
  );

  readonly ESTADO_LABELS   = ESTADO_LABELS;
  readonly ESTADO_SEVERITY = ESTADO_SEVERITY;
  readonly TIPO_LABELS     = TIPO_LABELS;

  readonly ACCIONES_ESTADO: Partial<Record<EstadoProyecto, { label: string; estado: EstadoProyecto; color: 'primary' | 'warn' | 'accent' }[]>> = {
    draft:       [{ label: 'Planificar', estado: 'planned', color: 'primary' }],
    planned:     [
      { label: 'Iniciar ejecución', estado: 'in_progress', color: 'primary' },
      { label: 'Volver a borrador', estado: 'draft', color: 'warn' },
    ],
    in_progress: [
      { label: 'Suspender', estado: 'suspended', color: 'warn' },
      { label: 'Cerrar', estado: 'closed', color: 'accent' },
    ],
    suspended: [{ label: 'Reactivar', estado: 'in_progress', color: 'primary' }],
  };

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) { this.router.navigate(['/proyectos']); return; }
    this.loadProyecto(id);
  }

  private loadProyecto(id: string): void {
    this.loading.set(true);
    this.proyectoService.getById(id).subscribe({
      next: (p) => { this.proyecto.set(p); this.loading.set(false); },
      error: () => {
        this.toast.error('No se pudo cargar el proyecto.');
        this.loading.set(false);
      },
    });
  }

  // ── SK-42: Auto-Schedule dialog ──────────────────────────────────────────

  openAutoSchedule(): void {
    const p = this.proyecto();
    if (!p) return;
    this.dialog.open(AutoScheduleDialogComponent, {
      data: { projectId: p.id, projectName: p.nombre },
      width: '560px',
      disableClose: false,
    });
  }

  editarProyecto(): void {
    const id = this.proyecto()?.id;
    if (id) this.router.navigate(['/proyectos', id, 'editar']);
  }

  cambiarEstado(nuevo_estado: EstadoProyecto): void {
    const p = this.proyecto();
    if (!p) return;
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: { header: 'Confirmar cambio de estado', message: `¿Cambiar el estado a "${ESTADO_LABELS[nuevo_estado]}"?`, acceptLabel: 'Confirmar', acceptColor: 'primary' },
      width: '400px',
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.proyectoService.cambiarEstado(p.id, nuevo_estado).subscribe({
        next: (updated) => {
          this.proyecto.set(updated);
          this.toast.success(`Proyecto en estado "${ESTADO_LABELS[nuevo_estado]}".`);
        },
        error: (err) => {
          const detail = (err as { error?: unknown[] | { detail?: string } })?.error;
          const msg = Array.isArray(detail) ? detail[0] : (detail as { detail?: string })?.detail ?? 'No se pudo cambiar el estado.';
          this.toast.error(String(msg));
        },
      });
    });
  }

  formatCurrency(value: string): string {
    const num = parseFloat(value);
    return isNaN(num) ? value : num.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
  }

  formatDate(date: string | null): string {
    if (!date) return '—';
    return new Date(date + 'T00:00:00').toLocaleDateString('es-CO');
  }
}
