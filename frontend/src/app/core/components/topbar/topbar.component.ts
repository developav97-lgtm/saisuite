import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Output,
  computed,
  inject,
  input,
} from '@angular/core';
import { Router, NavigationEnd, RouterModule } from '@angular/router';
import { filter, map } from 'rxjs/operators';
import { toSignal } from '@angular/core/rxjs-interop';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { ThemeService } from '../../services/theme.service';
import { AuthService } from '../../auth/auth.service';
import { NotificationBellComponent } from '../notification-bell/notification-bell.component';

const MODULO_LABELS: Record<string, string> = {
  dashboard:      'Dashboard',
  crm:            'CRM',
  soporte:        'Soporte',
  proyectos:      'Proyectos',
  terceros:       'Terceros',
  admin:          'Administración',
  notificaciones: 'Notificaciones',
};

const ROLE_LABELS: Record<string, string> = {
  company_admin:  'Administrador',
  seller:         'Vendedor',
  collector:      'Cobrador',
  viewer:         'Visualizador',
  valmen_admin:   'Admin Plataforma',
  valmen_support: 'Soporte',
};

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [RouterModule, MatIconModule, MatButtonModule, MatTooltipModule, MatMenuModule, MatDividerModule, NotificationBellComponent],
  templateUrl: './topbar.component.html',
  styleUrls: ['./topbar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TopbarComponent {
  readonly sidebarVisible = input(true);
  @Output() toggleSidebar = new EventEmitter<void>();

  readonly themeService = inject(ThemeService);
  readonly authService  = inject(AuthService);
  readonly currentUser  = inject(AuthService).currentUser;

  private readonly router = inject(Router);

  private readonly currentUrl = toSignal(
    this.router.events.pipe(
      filter(e => e instanceof NavigationEnd),
      map(e => (e as NavigationEnd).urlAfterRedirects),
    ),
    { initialValue: this.router.url },
  );

  readonly moduloActual = computed(() => {
    const segment = (this.currentUrl() ?? '').split('/')[1];
    return MODULO_LABELS[segment] ?? '';
  });

  readonly rolLabel = computed(() => {
    const user = this.currentUser();
    if (user?.is_superadmin || user?.is_superuser) return 'Super Admin';
    if (user?.is_staff) return 'Soporte';
    const role = user?.role ?? '';
    return ROLE_LABELS[role] ?? role;
  });

  readonly perfilUrl = computed(() => {
    const id = this.currentUser()?.id;
    return id ? `/admin/usuarios/${id}` : '/admin/usuarios';
  });

  /** Empresa activa visible en el topbar (para soporte y usuarios de tenant). */
  readonly empresaActiva = computed(() => {
    const user = this.currentUser();
    if (!user || user.is_superadmin || user.is_superuser) return null;
    const ec = user.effective_company ?? user.company;
    return ec ? { name: ec.name, isSoporte: !!user.is_staff } : null;
  });
}
