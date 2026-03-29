/**
 * SaiSuite — ProyectoDashboardComponent
 * Landing del módulo de proyectos: KPIs globales y estado de proyectos activos.
 */
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
import { Router } from '@angular/router';
import { DecimalPipe } from '@angular/common';
import { map, switchMap } from 'rxjs';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatRippleModule } from '@angular/material/core';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ProyectoService } from '../../services/proyecto.service';
import { ProyectoList, EstadoProyecto, ESTADO_LABELS } from '../../models/proyecto.model';
import { AnalyticsService } from '../../services/analytics.service';
import { ProjectComparison } from '../../models/analytics.model';

interface ProyectoKpi {
  id: string;
  nombre: string;
  completion_rate: number;
  total_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  on_time_rate: number;
  budget_variance: number | null;
}

interface EstadoCount { estado: EstadoProyecto; label: string; count: number; }

@Component({
  selector: 'app-proyecto-dashboard',
  templateUrl: './proyecto-dashboard.component.html',
  styleUrl: './proyecto-dashboard.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DecimalPipe,
    MatIconModule, MatButtonModule,
    MatProgressBarModule, MatRippleModule, MatTooltipModule,
  ],
})
export class ProyectoDashboardComponent implements OnInit {
  private readonly proyectoService  = inject(ProyectoService);
  private readonly analyticsService = inject(AnalyticsService);
  private readonly router           = inject(Router);
  private readonly destroyRef       = inject(DestroyRef);

  readonly proyectos    = signal<ProyectoList[]>([]);
  readonly loadingLista = signal(false);
  readonly kpis         = signal<ProyectoKpi[]>([]);
  readonly loadingKpis  = signal(false);

  // ── Agregados ──────────────────────────────────────────────
  readonly totalProyectos = computed(() => this.proyectos().length);

  readonly presupuestoTotal = computed(() =>
    this.proyectos().reduce((acc, p) => acc + (parseFloat(p.presupuesto_total) || 0), 0)
  );

  readonly overdueTotal = computed(() =>
    this.kpis().reduce((acc, k) => acc + k.overdue_tasks, 0)
  );

  readonly activosTotal = computed(() =>
    this.proyectos().filter(p => p.estado === 'planned' || p.estado === 'in_progress').length
  );

  readonly porEstado = computed<EstadoCount[]>(() => {
    const counts: Partial<Record<EstadoProyecto, number>> = {};
    for (const p of this.proyectos()) {
      counts[p.estado] = (counts[p.estado] ?? 0) + 1;
    }
    return (Object.entries(counts) as [EstadoProyecto, number][]).map(([estado, count]) => ({
      estado,
      label: ESTADO_LABELS[estado] ?? estado,
      count,
    }));
  });

  ngOnInit(): void {
    this.loadProyectos();
  }

  private loadProyectos(): void {
    this.loadingLista.set(true);
    this.proyectoService.list({ page_size: 200 }).pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (res) => {
        this.proyectos.set(res.results);
        this.loadingLista.set(false);
        this.loadKpis(res.results);
      },
      error: () => this.loadingLista.set(false),
    });
  }

  private loadKpis(todos: ProyectoList[]): void {
    const ids = todos
      .filter(p => p.estado === 'planned' || p.estado === 'in_progress')
      .map(p => p.id);

    if (ids.length === 0) { this.kpis.set([]); return; }

    this.loadingKpis.set(true);
    this.analyticsService.compareProjects({ project_ids: ids }).pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (comparisons: ProjectComparison[]) => {
        this.kpis.set(comparisons.map(c => ({
          id:             c.project_id,
          nombre:         c.project_name,
          completion_rate: c.completion_rate,
          total_tasks:    c.total_tasks,
          completed_tasks: c.completed_tasks,
          overdue_tasks:  c.overdue_tasks,
          on_time_rate:   c.on_time_rate,
          budget_variance: c.budget_variance,
        })));
        this.loadingKpis.set(false);
      },
      error: () => this.loadingKpis.set(false),
    });
  }

  estadoSalud(k: ProyectoKpi): string {
    if (k.overdue_tasks > 0 || k.on_time_rate < 60) return 'delayed';
    if (k.on_time_rate < 80) return 'at_risk';
    return 'on_track';
  }

  estadoSaludLabel(k: ProyectoKpi): string {
    const s = this.estadoSalud(k);
    if (s === 'on_track') return 'Al día';
    if (s === 'at_risk')  return 'En riesgo';
    return 'Atrasado';
  }

  estadoClass(estado: EstadoProyecto): string {
    return `pd-estado-chip pd-estado-chip--${estado}`;
  }

  formatCurrency(value: number): string {
    return value.toLocaleString('es-CO', {
      style: 'currency', currency: 'COP', maximumFractionDigits: 0,
    });
  }

  irALista(): void { this.router.navigate(['/proyectos', 'lista']); }
  irAProyecto(id: string): void { this.router.navigate(['/proyectos', id]); }
  nuevoProyecto(): void { this.router.navigate(['/proyectos', 'nuevo']); }
}
