/**
 * SaiSuite — Module Selector (Dashboard)
 * Landing post-login: grid de módulos disponibles.
 */
import {
  ChangeDetectionStrategy,
  Component,
  inject,
} from '@angular/core';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';
import { MatTooltipModule } from '@angular/material/tooltip';
import { AuthService } from '../../core/auth/auth.service';

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

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [MatIconModule, MatRippleModule, MatTooltipModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardComponent {
  private readonly router = inject(Router);
  readonly auth         = inject(AuthService);

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

  goTo(mod: AppModule): void {
    if (mod.available) this.router.navigate([mod.route]);
  }
}
