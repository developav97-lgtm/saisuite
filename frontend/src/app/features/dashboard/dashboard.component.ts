/**
 * SaiSuite — Module Selector (Dashboard)
 * Landing post-login: grid de módulos disponibles.
 * `available` se deriva de los módulos incluidos en la licencia de la empresa.
 * Los módulos de acceso universal (admin, terceros, proyectos) siempre están disponibles.
 */
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
} from '@angular/core';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';
import { MatTooltipModule } from '@angular/material/tooltip';
import { AuthService } from '../../core/auth/auth.service';

interface AppModuleDef {
  key: string;
  label: string;
  description: string;
  icon: string;
  route: string;
  color: string;
  /** true = siempre disponible sin necesitar licencia de módulo */
  alwaysAvailable?: boolean;
  badge?: string;
}

interface AppModule extends AppModuleDef {
  available: boolean;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [MatIconModule, MatRippleModule, MatTooltipModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly auth   = inject(AuthService);

  ngOnInit(): void {
    // Refresca el perfil para reflejar cambios de licencia sin necesidad de re-login.
    this.auth.refreshUserProfile().subscribe({ error: () => {} });
  }

  private readonly MODULOS_DEF: AppModuleDef[] = [
    {
      key: 'proyectos',
      label: 'Gestión de Proyectos',
      description: 'Proyectos, fases, tareas y seguimiento de avance',
      icon: 'engineering',
      route: '/proyectos',
      color: '#1565c0',
      alwaysAvailable: true,
    },
    {
      key: 'terceros',
      label: 'Terceros',
      description: 'Clientes, proveedores y aliados comerciales',
      icon: 'contacts',
      route: '/terceros',
      color: '#2e7d32',
      alwaysAvailable: true,
    },
    {
      key: 'crm',
      label: 'CRM',
      description: 'Pipeline de ventas, leads y cotizaciones',
      icon: 'storefront',
      route: '/crm',
      color: '#e65100',
    },
    {
      key: 'soporte',
      label: 'Soporte',
      description: 'Cartera, gestiones de cobro y pagos',
      icon: 'account_balance_wallet',
      route: '/soporte-module',
      color: '#6a1b9a',
    },
    {
      key: 'dashboard',
      label: 'Reportes',
      description: 'Reportes BI, dashboards financieros e indicadores contables',
      icon: 'analytics',
      route: '/saidashboard',
      color: '#1565c0',
      badge: 'Nuevo',
    },
    {
      key: 'admin',
      label: 'Administración',
      description: 'Usuarios, empresa, consecutivos y configuración',
      icon: 'admin_panel_settings',
      route: '/admin/usuarios',
      color: '#37474f',
      alwaysAvailable: true,
    },
  ];

  readonly modulos = computed<AppModule[]>(() => {
    const user     = this.auth.currentUser();
    const included: string[] = user?.company?.license?.modules_included ?? [];

    return this.MODULOS_DEF.map(def => ({
      ...def,
      available: def.alwaysAvailable === true || included.includes(def.key),
      badge: def.alwaysAvailable || included.includes(def.key) ? def.badge : (def.badge ?? 'Próximamente'),
    }));
  });

  goTo(mod: AppModule): void {
    if (mod.available) this.router.navigate([mod.route]);
  }
}
