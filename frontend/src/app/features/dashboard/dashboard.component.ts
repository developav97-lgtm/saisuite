/**
 * SaiSuite — Module Selector (Dashboard)
 * Landing post-login: KPIs de proyectos activos + grid de módulos disponibles.
 */
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { switchMap, map } from 'rxjs/operators';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatRippleModule } from '@angular/material/core';
import { MatTooltipModule } from '@angular/material/tooltip';
import { DecimalPipe } from '@angular/common';
import { AuthService } from '../../core/auth/auth.service';
import { ProyectoService } from '../proyectos/services/proyecto.service';
import { AnalyticsService } from '../proyectos/services/analytics.service';
import { ProjectComparison } from '../proyectos/models/analytics.model';

interface AppModule {
  key: string;
  label: string;
  description: string;
  icon: string;
  route: string;
  color: string;
  available: boolean;
  badge?: string;
}

/** Vista aplanada para las tarjetas de KPI del dashboard */
interface DashboardProjectKpi {
  id: string;
  nombre: string;
  codigo: string;
  porcentaje_avance: number;
  total_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  on_time_rate: number;
  velocity: number;
  budget_variance: number | null;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [MatIconModule, MatProgressBarModule, MatRippleModule, MatTooltipModule, DecimalPipe],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardComponent implements OnInit {
  private readonly router           = inject(Router);
  private readonly destroyRef       = inject(DestroyRef);
  private readonly proyectoService  = inject(ProyectoService);
  private readonly analyticsService = inject(AnalyticsService);
  readonly auth                     = inject(AuthService);

  readonly proyectosKpis = signal<DashboardProjectKpi[]>([]);
  readonly loadingKpis   = signal(false);

  readonly modulos: AppModule[] = [
    {
      key: 'proyectos',
      label: 'Gestión de Proyectos',
      description: 'Proyectos, fases, tareas y seguimiento de avance',
      icon: 'engineering',
      route: '/proyectos',
      color: '#1565c0',
      available: true,
    },
    {
      key: 'terceros',
      label: 'Terceros',
      description: 'Clientes, proveedores y aliados comerciales',
      icon: 'contacts',
      route: '/terceros',
      color: '#2e7d32',
      available: true,
    },
    {
      key: 'ventas',
      label: 'SaiVentas',
      description: 'Pedidos, clientes y catálogo de productos',
      icon: 'storefront',
      route: '/ventas',
      color: '#e65100',
      available: false,
      badge: 'Próximamente',
    },
    {
      key: 'cobros',
      label: 'SaiCobros',
      description: 'Cartera, gestiones de cobro y pagos',
      icon: 'account_balance_wallet',
      route: '/cobros',
      color: '#6a1b9a',
      available: false,
      badge: 'Próximamente',
    },
    {
      key: 'admin',
      label: 'Administración',
      description: 'Usuarios, empresa, módulos y configuración',
      icon: 'admin_panel_settings',
      route: '/admin/usuarios',
      color: '#37474f',
      available: true,
    },
    {
      key: 'config',
      label: 'Configuración',
      description: 'Preferencias del sistema y parámetros globales',
      icon: 'settings',
      route: '/configuracion',
      color: '#00796b',
      available: true,
    },
  ];

  ngOnInit(): void {
    this.cargarKpis();
  }

  private cargarKpis(): void {
    this.loadingKpis.set(true);

    // 1. Listar proyectos activos (estados operativos: planned, in_progress)
    // 2. Con sus IDs, llamar al endpoint compare para obtener KPIs
    this.proyectoService
      .list({ activo: true, page_size: 50 })
      .pipe(
        map(paginated => paginated.results
          .filter(p => p.estado === 'planned' || p.estado === 'in_progress')
          .map(p => p.id)
        ),
        switchMap(ids => {
          if (ids.length === 0) {
            return [[] as ProjectComparison[]];
          }
          return this.analyticsService.compareProjects({ project_ids: ids });
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (comparisons) => {
          const kpis: DashboardProjectKpi[] = comparisons.map(c => ({
            id:               c.project_id,
            nombre:           c.project_name,
            codigo:           c.project_code,
            porcentaje_avance: c.completion_rate,
            total_tasks:      c.total_tasks,
            completed_tasks:  c.completed_tasks,
            overdue_tasks:    c.overdue_tasks,
            on_time_rate:     c.on_time_rate,
            velocity:         c.velocity,
            budget_variance:  c.budget_variance ?? null,
          }));
          this.proyectosKpis.set(kpis);
          this.loadingKpis.set(false);
        },
        error: () => {
          this.loadingKpis.set(false);
        },
      });
  }

  irAProyecto(id: string): void {
    void this.router.navigate(['/proyectos', id]);
  }

  /**
   * Clasifica el estado de salud del proyecto según sus KPIs:
   * - "on_track": sin tareas vencidas y on_time_rate >= 80
   * - "at_risk": algunas tareas vencidas o on_time_rate entre 50 y 79
   * - "delayed": muchas tareas vencidas o on_time_rate < 50
   */
  estadoSalud(kpi: DashboardProjectKpi): 'on_track' | 'at_risk' | 'delayed' {
    if (kpi.overdue_tasks === 0 && kpi.on_time_rate >= 80) return 'on_track';
    if (kpi.on_time_rate < 50 || (kpi.overdue_tasks > 0 && kpi.total_tasks > 0 && kpi.overdue_tasks / kpi.total_tasks > 0.3)) return 'delayed';
    return 'at_risk';
  }

  estadoSaludLabel(kpi: DashboardProjectKpi): string {
    const s = this.estadoSalud(kpi);
    const labels: Record<string, string> = { on_track: 'Al día', at_risk: 'En riesgo', delayed: 'Retrasado' };
    return labels[s] ?? s;
  }

  goTo(mod: AppModule): void {
    if (mod.available) this.router.navigate([mod.route]);
  }
}
