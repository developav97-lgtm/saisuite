import {
  AfterViewInit, ChangeDetectionStrategy, Component, OnInit,
  ViewChild, computed, effect, inject, signal,
} from '@angular/core';
import { RouterModule } from '@angular/router';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSortModule, MatSort } from '@angular/material/sort';
import { AdminService } from '../services/admin.service';
import { AdminUser, UserRole, ROLE_LABELS, ROLE_OPTIONS } from '../models/admin.models';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../core/services/toast.service';

@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.html',
  styleUrl: './user-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatChipsModule, MatTooltipModule, MatDialogModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatProgressBarModule, MatPaginatorModule, MatSortModule,
  ],
})
export class UserListComponent implements OnInit, AfterViewInit {
  private readonly adminService = inject(AdminService);
  private readonly dialog       = inject(MatDialog);
  private readonly toast       = inject(ToastService);

  readonly users       = signal<AdminUser[]>([]);
  readonly loading     = signal(false);

  readonly dataSource = new MatTableDataSource<AdminUser>([]);
  @ViewChild(MatSort) sort!: MatSort;

  constructor() {
    effect(() => {
      this.dataSource.data = this.users();
    });
  }

  ngAfterViewInit(): void {
    this.dataSource.sort = this.sort;
  }
  readonly totalCount  = signal(0);
  readonly currentPage = signal(1);
  readonly pageSize    = 25;

  readonly searchText  = signal('');
  readonly roleFilter  = signal<UserRole | ''>('');
  readonly activeFilter = signal<boolean | ''>('');

  readonly hayFiltros = computed(() =>
    !!this.searchText() || !!this.roleFilter() || this.activeFilter() !== '',
  );

  readonly displayedColumns = ['nombre', 'email', 'rol', 'estado', 'acciones'];

  readonly roleOptions: { value: UserRole | ''; label: string }[] = [
    { value: '', label: 'Todos los roles' },
    ...ROLE_OPTIONS,
  ];

  readonly activeOptions: { value: boolean | ''; label: string }[] = [
    { value: '',    label: 'Todos'     },
    { value: true,  label: 'Activos'   },
    { value: false, label: 'Inactivos' },
  ];

  getRoleLabel(role: string): string {
    return ROLE_LABELS[role as UserRole] ?? role;
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.adminService.listUsers({
      search:    this.searchText() || undefined,
      role:      this.roleFilter()   || undefined,
      is_active: this.activeFilter() !== '' ? this.activeFilter() as boolean : undefined,
      page:      this.currentPage(),
      page_size: this.pageSize,
    }).subscribe({
      next: (data) => {
        this.users.set(data.results ?? []);
        this.totalCount.set(data.count ?? 0);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('Error al cargar usuarios.');
        this.loading.set(false);
      },
    });
  }

  onSearch(): void {
    this.currentPage.set(1);
    this.load();
  }

  aplicarFiltros(): void {
    this.currentPage.set(1);
    this.load();
  }

  limpiarFiltros(): void {
    this.searchText.set('');
    this.roleFilter.set('');
    this.activeFilter.set('');
    this.currentPage.set(1);
    this.load();
  }

  onPageChange(event: PageEvent): void {
    this.currentPage.set(event.pageIndex + 1);
    this.load();
  }

  confirmarDesactivar(user: AdminUser): void {
    if (!user.is_active) return;
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header:      'Desactivar usuario',
        message:     `¿Desactivar al usuario "${user.full_name}"? No podrá ingresar al sistema.`,
        acceptLabel: 'Desactivar',
        acceptColor: 'warn',
      },
      width: '400px',
    });
    ref.afterClosed().subscribe((ok: boolean) => {
      if (!ok) return;
      this.adminService.deactivateUser(user.id).subscribe({
        next: (updated) => {
          this.users.update(list => list.map(u => u.id === updated.id ? updated : u));
          this.toast.success('Usuario desactivado.');
        },
        error: () => this.toast.error('No se pudo desactivar.'),
      });
    });
  }

  confirmarActivar(user: AdminUser): void {
    if (user.is_active) return;
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header:      'Activar usuario',
        message:     `¿Reactivar al usuario "${user.full_name}"? Podrá ingresar al sistema nuevamente.`,
        acceptLabel: 'Activar',
        acceptColor: 'primary',
      },
      width: '400px',
    });
    ref.afterClosed().subscribe((ok: boolean) => {
      if (!ok) return;
      this.adminService.activateUser(user.id).subscribe({
        next: (updated) => {
          this.users.update(list => list.map(u => u.id === updated.id ? updated : u));
          this.toast.success('Usuario activado.');
        },
        error: () => this.toast.error('No se pudo activar.'),
      });
    });
  }
}
