import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ResponsiveTableDirective } from '../../../shared/directives';
import { Role, RolesService, TIPO_LABELS } from '../services/roles.service';
import { RoleFormComponent } from './role-form.component';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../core/services/toast.service';
import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-roles-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ResponsiveTableDirective,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
    MatDialogModule,
    MatProgressBarModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatPaginatorModule,
  ],
  templateUrl: './roles-list.component.html',
  styleUrl: './roles-list.component.scss',
})
export class RolesListComponent implements OnInit {
  private readonly rolesService = inject(RolesService);
  private readonly dialog       = inject(MatDialog);
  private readonly toast        = inject(ToastService);
  private readonly authService  = inject(AuthService);

  get licenseModules(): string[] {
    const user = this.authService.currentUser();
    const ec = user?.effective_company ?? user?.company;
    return ec?.license?.modules_included ?? [];
  }

  readonly loading    = signal(false);
  readonly allRoles   = signal<Role[]>([]);
  readonly roles      = signal<Role[]>([]);
  readonly totalCount = signal(0);
  readonly currentPage = signal(1);
  readonly pageSize    = 25;

  readonly searchText  = signal('');
  readonly tipoFilter  = signal<Role['tipo'] | ''>('');

  readonly tipoOptions: { value: Role['tipo'] | ''; label: string }[] = [
    { value: '',         label: 'Todos los tipos' },
    { value: 'admin',    label: 'Administrador'   },
    { value: 'readonly', label: 'Solo Lectura'    },
    { value: 'custom',   label: 'Personalizado'   },
  ];

  readonly columnas = ['nombre', 'tipo', 'descripcion', 'permisos', 'usuarios', 'acciones'];

  ngOnInit(): void {
    this.cargar();
  }

  private cargar(): void {
    this.loading.set(true);
    this.rolesService.listar().subscribe({
      next: data => {
        this.allRoles.set(data);
        this.aplicarFiltrosLocal();
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  private aplicarFiltrosLocal(): void {
    let filtrados = this.allRoles();
    const q     = this.searchText().toLowerCase().trim();
    const tipo  = this.tipoFilter();

    if (q)    filtrados = filtrados.filter(r => r.nombre.toLowerCase().includes(q) || r.descripcion.toLowerCase().includes(q));
    if (tipo) filtrados = filtrados.filter(r => r.tipo === tipo);

    this.totalCount.set(filtrados.length);
    const start = (this.currentPage() - 1) * this.pageSize;
    this.roles.set(filtrados.slice(start, start + this.pageSize));
  }

  onSearch(): void {
    this.currentPage.set(1);
    this.aplicarFiltrosLocal();
  }

  aplicarFiltros(): void {
    this.currentPage.set(1);
    this.aplicarFiltrosLocal();
  }

  limpiarFiltros(): void {
    this.searchText.set('');
    this.tipoFilter.set('');
    this.currentPage.set(1);
    this.aplicarFiltrosLocal();
  }

  onPageChange(event: PageEvent): void {
    this.currentPage.set(event.pageIndex + 1);
    this.aplicarFiltrosLocal();
  }

  hayFiltros(): boolean {
    return !!this.searchText() || !!this.tipoFilter();
  }

  getTipoLabel(tipo: Role['tipo']): string {
    return TIPO_LABELS[tipo] ?? tipo;
  }

  crearRol(): void {
    this.dialog
      .open(RoleFormComponent, { data: { mode: 'create', licenseModules: this.licenseModules }, width: '1100px', maxWidth: '96vw', maxHeight: '95vh' })
      .afterClosed()
      .subscribe(result => {
        if (result) { this.toast.success('Rol creado correctamente'); this.cargar(); }
      });
  }

  editarRol(rol: Role): void {
    this.dialog
      .open(RoleFormComponent, { data: { mode: 'edit', rol, licenseModules: this.licenseModules }, width: '1100px', maxWidth: '96vw', maxHeight: '95vh' })
      .afterClosed()
      .subscribe(result => {
        if (result) { this.toast.success('Rol actualizado correctamente'); this.cargar(); }
      });
  }

  eliminarRol(rol: Role): void {
    this.dialog
      .open(ConfirmDialogComponent, {
        data: {
          title:        'Eliminar Rol',
          message:      `¿Estás seguro de eliminar el rol "${rol.nombre}"? Esta acción no se puede deshacer.`,
          confirmText:  'Eliminar',
          confirmColor: 'warn',
        },
      })
      .afterClosed()
      .subscribe(confirmed => {
        if (!confirmed) return;
        this.rolesService.eliminar(rol.id).subscribe({
          next: () => { this.toast.success('Rol eliminado'); this.cargar(); },
          error: (err: { error?: { error?: string } }) => {
            this.toast.error(err?.error?.error ?? 'Error al eliminar rol');
          },
        });
      });
  }
}
