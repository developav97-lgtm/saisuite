import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  HostListener,
  OnInit,
  Output,
  inject,
  input,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';

export interface NavItem {
  label: string;
  icon: string;
  route?: string;
  badge?: string | number;
  children?: NavItem[];
}

export interface NavSection {
  sectionLabel?: string;
  items: NavItem[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SidebarComponent implements OnInit {
  readonly visible = input(true);
  @Output() visibleChange = new EventEmitter<boolean>();

  private readonly cdr = inject(ChangeDetectorRef);

  isDesktop = true;
  expandedItems = new Set<string>();

  navSections: NavSection[] = [
    {
      items: [
        { label: 'Dashboard', icon: 'home', route: '/dashboard' },
      ],
    },
    {
      sectionLabel: 'Módulos',
      items: [
        {
          label: 'SaiVentas',
          icon: 'shopping_cart',
          children: [
            { label: 'Clientes', icon: 'group', route: '/ventas/clientes' },
            { label: 'Pedidos', icon: 'list', route: '/ventas/pedidos' },
            { label: 'Productos', icon: 'inventory_2', route: '/ventas/productos' },
          ],
        },
        {
          label: 'SaiCobros',
          icon: 'account_balance_wallet',
          children: [
            { label: 'Cartera', icon: 'attach_money', route: '/cobros/cartera' },
            { label: 'Gestiones', icon: 'phone', route: '/cobros/gestiones' },
            { label: 'Pagos', icon: 'check_circle', route: '/cobros/pagos' },
          ],
        },
        {
          label: 'Proyectos',
          icon: 'work',
          children: [
            { label: 'Lista', icon: 'list', route: '/proyectos' },
            { label: 'Nuevo', icon: 'add', route: '/proyectos/nuevo' },
            { label: 'Catálogo de actividades', icon: 'construction', route: '/proyectos/actividades' },
          ],
        },
      ],
    },
    {
      sectionLabel: 'Sistema',
      items: [
        { label: 'Configuración', icon: 'settings', route: '/configuracion' },
        {
          label: 'Administración',
          icon: 'admin_panel_settings',
          children: [
            { label: 'Usuarios',      icon: 'group',    route: '/admin/usuarios' },
            { label: 'Empresa',       icon: 'business', route: '/admin/empresa' },
            { label: 'Módulos',       icon: 'apps',     route: '/admin/modulos' },
            { label: 'Consecutivos',  icon: 'tag',      route: '/admin/consecutivos' },
          ],
        },
      ],
    },
  ];

  ngOnInit(): void {
    this.checkBreakpoint();
  }

  @HostListener('window:resize')
  onResize(): void {
    this.checkBreakpoint();
    this.cdr.markForCheck();
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

  closeDrawer(): void {
    this.visibleChange.emit(false);
  }

  private checkBreakpoint(): void {
    this.isDesktop = window.innerWidth >= 992;
  }
}
