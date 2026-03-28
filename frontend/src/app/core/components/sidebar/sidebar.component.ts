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

const TAREAS_VIEW_KEY = 'saisuite.tareasView';

export interface NavItem {
  label: string;
  icon: string;
  route?: string;
  action?: () => void;
  badge?: string | number;
  children?: NavItem[];
  exact?: boolean;
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

  private readonly cdr    = inject(ChangeDetectorRef);
  private readonly router = inject(Router);
  private readonly dialog = inject(MatDialog);
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
        { label: 'Proyectos',       icon: 'engineering',         route: '/proyectos' },
        { label: 'Terceros',        icon: 'contacts',            route: '/terceros' },
        { label: 'Administración',  icon: 'admin_panel_settings', route: '/admin/usuarios' },
        { label: 'Configuración',   icon: 'settings',            route: '/configuracion' },
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
          { label: 'Proyectos',     icon: 'work',         route: '/proyectos',              exact: true },
          { label: 'Actividades',   icon: 'construction', route: '/proyectos/actividades' },
          {
            label: 'Tareas',
            icon: 'task_alt',
            action: () => this.navigateToTareas(),
          },
          { label: 'Timesheets',    icon: 'schedule',     route: '/proyectos/timesheets' },
          { label: 'Mis Tareas',    icon: 'person',       route: '/proyectos/mis-tareas' },
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

  private readonly ADMIN_NAV: NavSection[] = [
    {
      items: [
        { label: 'Módulos', icon: 'apps', route: '/dashboard' },
      ],
    },
    {
      sectionLabel: 'Administración',
      items: [
        { label: 'Usuarios',     icon: 'manage_accounts', route: '/admin/usuarios' },
        { label: 'Empresa',      icon: 'business',        route: '/admin/empresa' },
        { label: 'Módulos',      icon: 'extension',       route: '/admin/modulos' },
        { label: 'Consecutivos', icon: 'tag',             route: '/admin/consecutivos' },
      ],
    },
  ];

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

  private readonly CONFIG_NAV: NavSection[] = [
    {
      items: [
        { label: 'Módulos', icon: 'apps', route: '/dashboard' },
      ],
    },
    {
      sectionLabel: 'Configuración',
      items: [
        { label: 'Sistema', icon: 'settings', route: '/configuracion' },
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
    const mod = this.detectModule(url);
    switch (mod) {
      case 'proyectos': this.navSections = this.PROYECTOS_NAV; break;
      case 'admin':     this.navSections = this.ADMIN_NAV;     break;
      case 'terceros':  this.navSections = this.TERCEROS_NAV;  break;
      case 'config':    this.navSections = this.CONFIG_NAV;    break;
      default:          this.navSections = this.HOME_NAV;
    }
  }

  private detectModule(url: string): string {
    if (url.startsWith('/proyectos'))    return 'proyectos';
    if (url.startsWith('/admin'))        return 'admin';
    if (url.startsWith('/terceros'))     return 'terceros';
    if (url.startsWith('/configuracion')) return 'config';
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

  isTareasActive(): boolean {
    return this.router.url.startsWith('/proyectos/tareas');
  }

  closeDrawer(): void {
    this.visibleChange.emit(false);
  }

  private checkBreakpoint(): void {
    this.isDesktop = window.innerWidth >= 992;
  }
}
