import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  OnDestroy,
  OnInit,
  Output,
  Type,
  inject,
  input,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, NavigationEnd } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { MatDialogModule } from '@angular/material/dialog';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { QuickAccessRoute } from '../../../shared/services/quick-access-navigator.service';
import { AuthService } from '../../auth/auth.service';

const TAREAS_VIEW_KEY = 'saisuite.tareasView';

export interface NavItem {
  label: string;
  icon: string;
  route?: string;
  action?: () => void;
  activeCheck?: () => boolean;
  badge?: string | number;
  children?: NavItem[];
  exact?: boolean;
  /** Código de permiso granular requerido para mostrar este ítem (ej: 'proyectos.view') */
  permission?: string;
}

export interface NavSection {
  sectionLabel?: string;
  items: NavItem[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule, MatTooltipModule, MatDialogModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SidebarComponent implements OnInit, OnDestroy {
  readonly visible = input(true);
  @Output() visibleChange = new EventEmitter<boolean>();

  private readonly cdr         = inject(ChangeDetectorRef);
  private readonly router      = inject(Router);
  private readonly dialog      = inject(MatDialog);
  private readonly authService = inject(AuthService);
  private routerSub?: Subscription;

  isDesktop      = true;
  expandedItems  = new Set<string>();
  navSections: NavSection[] = [];

  // ── Nav configs por módulo ──────────────────────────────────

  private readonly HOME_NAV: NavSection[] = [
    {
      items: [
        { label: 'Inicio', icon: 'home', route: '/dashboard', exact: true },
      ],
    },
    {
      sectionLabel: 'Módulos',
      items: [
        { label: 'Proyectos',       icon: 'engineering',          route: '/proyectos' },
        { label: 'SaiDashboard',    icon: 'bar_chart',            route: '/saidashboard' },
        { label: 'Terceros',        icon: 'contacts',             route: '/terceros' },
        { label: 'Administración',  icon: 'admin_panel_settings', route: '/admin/usuarios' },
      ],
    },
  ];

  private readonly SAIDASHBOARD_NAV: NavSection[] = [
    {
      items: [
        { label: 'Módulos', icon: 'apps', route: '/dashboard' },
      ],
    },
    {
      sectionLabel: 'SaiDashboard',
      items: [
        { label: 'Mis Dashboards', icon: 'bar_chart',    route: '/saidashboard', exact: true },
        { label: 'Nuevo Dashboard', icon: 'add_chart',   route: '/saidashboard/nuevo' },
      ],
    },
  ];

  private get PROYECTOS_NAV(): NavSection[] {
    return [
      {
        items: [
          { label: 'Módulos', icon: 'apps', route: '/dashboard' },
        ],
      },
      {
        sectionLabel: 'Gestión de Proyectos',
        items: [
          { label: 'Dashboard', icon: 'dashboard', route: '/proyectos/dashboard', exact: true, permission: 'proyectos.view' },
          {
            label: 'Proyectos',
            icon: 'work',
            action: () => this.router.navigate(['/proyectos/lista']),
            activeCheck: () => this.isProyectosListaActive(),
            permission: 'proyectos.view',
          },
          {
            label: 'Tareas',
            icon: 'task_alt',
            action: () => this.navigateToTareas(),
            activeCheck: () => this.isTareasActive(),
            permission: 'tareas.view',
          },
          {
            label: 'Mis Tareas',
            icon: 'person',
            action: () => this.navigateToMisTareas(),
            activeCheck: () => this.isMisTareasActive(),
            permission: 'tareas.view',
          },
          { label: 'Registro de Horas', icon: 'schedule', route: '/proyectos/timesheets', permission: 'timesheets.view' },
          { label: 'Actividades',   icon: 'construction', route: '/proyectos/actividades', permission: 'actividades.view' },
          { label: 'Configuración', icon: 'tune',         route: '/proyectos/configuracion' },
        ],
      },
      {
        sectionLabel: 'Acceso rápido',
        items: [
          {
            label: 'Terceros',
            icon: 'contacts',
            action: () => this.openQuickAccess(
              'Terceros',
              () => import('../../../features/terceros/pages/tercero-list-page/tercero-list-page.component')
                        .then(m => m.TerceroListPageComponent),
              [
                {
                  pattern: '/terceros/nuevo',
                  loader: () => import('../../../features/terceros/pages/tercero-form/tercero-form.component')
                                    .then(m => m.TerceroFormComponent),
                },
                {
                  pattern: '/terceros/:id/editar',
                  loader: () => import('../../../features/terceros/pages/tercero-form/tercero-form.component')
                                    .then(m => m.TerceroFormComponent),
                },
              ],
            ),
          },
          {
            label: 'Usuarios',
            icon: 'manage_accounts',
            action: () => this.openQuickAccess(
              'Usuarios',
              () => import('../../../features/admin/user-list/user-list.component')
                        .then(m => m.UserListComponent),
              [
                {
                  pattern: '/admin/usuarios/nuevo',
                  loader: () => import('../../../features/admin/user-form/user-form.component')
                                    .then(m => m.UserFormComponent),
                },
                {
                  pattern: '/admin/usuarios/:id',
                  loader: () => import('../../../features/admin/user-form/user-form.component')
                                    .then(m => m.UserFormComponent),
                },
              ],
            ),
          },
          {
            label: 'Consecutivos',
            icon: 'tag',
            action: () => this.openQuickAccess(
              'Consecutivos',
              () => import('../../../features/admin/consecutivos/consecutivo-list.component')
                        .then(m => m.ConsecutivoListComponent),
              [],
            ),
          },
        ],
      },
    ];
  }

  private get ADMIN_NAV(): NavSection[] {
    const user = this.authService.currentUser();
    const isSuperadmin = user?.is_superadmin || user?.role === 'valmen_admin';

    // SuperAdmin solo ve gestión de tenants y usuarios internos
    if (isSuperadmin) {
      return [
        {
          sectionLabel: 'Superadmin ValMen Tech',
          items: [
            { label: 'Tenants',           icon: 'domain',               route: '/admin/tenants' },
            { label: 'Paquetes',          icon: 'inventory_2',          route: '/admin/packages' },
            { label: 'Solicitudes',       icon: 'mark_email_unread',    route: '/admin/license-requests' },
            { label: 'Usuarios internos', icon: 'supervised_user_circle', route: '/admin/usuarios-internos' },
            { label: 'Base de Conocimiento IA', icon: 'auto_awesome',   route: '/admin/knowledge-base' },
          ],
        },
      ];
    }

    // Soporte ve los mismos items que un admin de empresa (sin tenants)
    return [
      {
        items: [
          { label: 'Módulos', icon: 'apps', route: '/dashboard' },
        ],
      },
      {
        sectionLabel: 'Administración',
        items: [
          { label: 'Usuarios',     icon: 'manage_accounts', route: '/admin/usuarios' },
          { label: 'Roles',        icon: 'security',        route: '/admin/roles' },
          { label: 'Empresa',      icon: 'business',        route: '/admin/empresa' },
          { label: 'Consecutivos', icon: 'tag',             route: '/admin/consecutivos' },
        ],
      },
    ];
  }

  private readonly TERCEROS_NAV: NavSection[] = [
    {
      items: [
        { label: 'Módulos', icon: 'apps', route: '/dashboard' },
      ],
    },
    {
      sectionLabel: 'Terceros',
      items: [
        { label: 'Listado', icon: 'contacts', route: '/terceros' },
      ],
    },
  ];

  // ── Ciclo de vida ────────────────────────────────────────────

  ngOnInit(): void {
    this.checkBreakpoint();
    this.updateNav(this.router.url);

    this.routerSub = this.router.events
      .pipe(filter(e => e instanceof NavigationEnd))
      .subscribe((e: NavigationEnd) => {
        this.updateNav(e.urlAfterRedirects);
        this.cdr.markForCheck();
      });
  }

  ngOnDestroy(): void {
    this.routerSub?.unsubscribe();
  }

  onResize(): void {
    this.checkBreakpoint();
    this.cdr.markForCheck();
  }

  // ── Lógica de navegación ─────────────────────────────────────

  private updateNav(url: string): void {
    const user = this.authService.currentUser();

    // SuperAdmin siempre ve el nav de admin — nunca el de modulos de tenant
    if (user?.is_superadmin || user?.role === 'valmen_admin') {
      this.navSections = this.ADMIN_NAV;
      return;
    }

    const mod = this.detectModule(url);
    let sections: NavSection[];
    switch (mod) {
      case 'proyectos':    sections = this.PROYECTOS_NAV;    break;
      case 'admin':        sections = this.ADMIN_NAV;        break;
      case 'terceros':     sections = this.TERCEROS_NAV;     break;
      case 'saidashboard': sections = this.SAIDASHBOARD_NAV; break;
      default:             sections = this.HOME_NAV;
    }

    // Filtrar ítems que requieren permiso que el usuario no tiene
    this.navSections = sections.map(section => ({
      ...section,
      items: section.items.filter(item => this._tienePermiso(item.permission)),
    }));
  }

  /** Verifica si el usuario tiene un permiso granular. Sin permiso definido → siempre visible. */
  private _tienePermiso(codigo?: string): boolean {
    if (!codigo) return true;
    const user = this.authService.currentUser();
    if (!user) return false;
    if (user.is_superadmin || user.role === 'valmen_admin' || user.is_staff) return true;
    const permisos = user.rol_granular?.permisos ?? [];
    return permisos.some(p => p.codigo === codigo);
  }

  private detectModule(url: string): string {
    if (url.startsWith('/proyectos'))    return 'proyectos';
    if (url.startsWith('/admin'))        return 'admin';
    if (url.startsWith('/terceros'))     return 'terceros';
    if (url.startsWith('/saidashboard')) return 'saidashboard';
    return 'home';
  }

  /** Abre un módulo en dialog overlay sin cambiar la URL ni el sidebar */
  private openQuickAccess(
    title: string,
    loader: () => Promise<Type<unknown>>,
    routes: QuickAccessRoute[],
  ): void {
    Promise.all([
      loader(),
      import('../../../shared/components/quick-access-dialog/quick-access-dialog.component'),
    ]).then(([component, m]) => {
      this.dialog.open(m.QuickAccessDialogComponent, {
        data: { title, component, routes },
        width: '92vw',
        maxWidth: '92vw',
        height: '88vh',
        panelClass: 'sc-quick-access-dialog',
      });
    });
  }

  /** Navega a la última vista de Tareas guardada (lista o kanban) */
  private navigateToTareas(): void {
    const view = localStorage.getItem(TAREAS_VIEW_KEY) ?? 'kanban';
    const route = view === 'kanban'
      ? '/proyectos/tareas/kanban'
      : '/proyectos/tareas';
    this.router.navigate([route]);
  }

  /** Navega a Mis Tareas respetando la última vista guardada */
  private navigateToMisTareas(): void {
    const view = localStorage.getItem(TAREAS_VIEW_KEY) ?? 'kanban';
    if (view === 'kanban') {
      this.router.navigate(['/proyectos/tareas/kanban'], { queryParams: { mis_tareas: '1' } });
    } else {
      this.router.navigate(['/proyectos/mis-tareas']);
    }
  }

  isMisTareasActive(): boolean {
    const url = this.router.url.split('?')[0];
    if (url === '/proyectos/mis-tareas') return true;
    if (url === '/proyectos/tareas/kanban') {
      return this.router.url.includes('mis_tareas=1');
    }
    return false;
  }

  // ── Template helpers ─────────────────────────────────────────

  handleItemClick(item: NavItem): void {
    if (item.action) {
      item.action();
    } else if (item.children) {
      this.toggleExpand(item.label);
    }
  }

  toggleExpand(label: string): void {
    if (this.expandedItems.has(label)) {
      this.expandedItems.delete(label);
    } else {
      this.expandedItems.add(label);
    }
    this.cdr.markForCheck();
  }

  isExpanded(label: string): boolean {
    return this.expandedItems.has(label);
  }

  isProyectosListaActive(): boolean {
    const url = this.router.url.split('?')[0];
    return url === '/proyectos/lista' || url === '/proyectos/cards';
  }

  isTareasActive(): boolean {
    if (!this.router.url.startsWith('/proyectos/tareas')) return false;
    // No marcar activo si es el kanban de "Mis Tareas"
    if (this.router.url.includes('mis_tareas=1')) return false;
    return true;
  }

  closeDrawer(): void {
    this.visibleChange.emit(false);
  }

  private checkBreakpoint(): void {
    this.isDesktop = window.innerWidth >= 992;
  }
}
