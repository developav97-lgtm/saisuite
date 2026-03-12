// frontend/src/app/core/components/sidebar/sidebar.component.ts
import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    HostListener,
    OnInit,
    ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { DrawerModule } from 'primeng/drawer';

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
    imports: [CommonModule, RouterModule, DrawerModule],
    templateUrl: './sidebar.component.html',
    styleUrls: ['./sidebar.component.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SidebarComponent implements OnInit {
    @Input() visible = true;
    @Output() visibleChange = new EventEmitter<boolean>();

    isDesktop = true;
    expandedItems = new Set<string>();

    // Navegación — ajustar cuando se confirmen módulos con Saiopen
    navSections: NavSection[] = [
        {
            items: [
                { label: 'Dashboard', icon: 'pi pi-home', route: '/dashboard' },
            ],
        },
        {
            sectionLabel: 'Módulos',
            items: [
                {
                    label: 'SaiVentas',
                    icon: 'pi pi-shopping-cart',
                    children: [
                        { label: 'Clientes', icon: 'pi pi-users', route: '/ventas/clientes' },
                        { label: 'Pedidos', icon: 'pi pi-list', route: '/ventas/pedidos' },
                        { label: 'Productos', icon: 'pi pi-box', route: '/ventas/productos' },
                    ],
                },
                {
                    label: 'SaiCobros',
                    icon: 'pi pi-wallet',
                    children: [
                        { label: 'Cartera', icon: 'pi pi-dollar', route: '/cobros/cartera' },
                        { label: 'Gestiones', icon: 'pi pi-phone', route: '/cobros/gestiones' },
                        { label: 'Pagos', icon: 'pi pi-check-circle', route: '/cobros/pagos' },
                    ],
                },
            ],
        },
        {
            sectionLabel: 'Sistema',
            items: [
                { label: 'Configuración', icon: 'pi pi-cog', route: '/configuracion' },
            ],
        },
    ];

    constructor(private cdr: ChangeDetectorRef) { }

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

    onDrawerHide(): void {
        this.visibleChange.emit(false);
    }

    private checkBreakpoint(): void {
        this.isDesktop = window.innerWidth >= 992;
    }
}