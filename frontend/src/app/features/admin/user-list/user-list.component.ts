import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AdminService } from '../services/admin.service';
import { AdminUser, ROLE_LABELS } from '../models/admin.models';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.html',
  styleUrl: './user-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, RouterModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatChipsModule, MatTooltipModule, MatProgressSpinnerModule,
    MatDialogModule,
  ],
})
export class UserListComponent implements OnInit {
  private readonly adminService = inject(AdminService);
  private readonly dialog       = inject(MatDialog);
  private readonly snackBar     = inject(MatSnackBar);

  readonly users   = signal<AdminUser[]>([]);
  readonly loading = signal(false);

  readonly displayedColumns = ['nombre', 'email', 'rol', 'estado', 'acciones'];

  getRoleLabel(role: string): string {
    return ROLE_LABELS[role as keyof typeof ROLE_LABELS] ?? role;
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.adminService.listUsers().subscribe({
      next: (data) => { this.users.set(data); this.loading.set(false); },
      error: ()     => { this.loading.set(false); },
    });
  }

  confirmarDesactivar(user: AdminUser): void {
    if (!user.is_active) return;
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Desactivar usuario',
        message: `¿Desactivar al usuario "${user.full_name}"? No podrá ingresar al sistema.`,
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
          this.snackBar.open('Usuario desactivado.', 'Cerrar', { duration: 3000 });
        },
        error: () => this.snackBar.open('No se pudo desactivar.', 'Cerrar', { duration: 5000 }),
      });
    });
  }

  confirmarActivar(user: AdminUser): void {
    if (user.is_active) return;
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Activar usuario',
        message: `¿Reactivar al usuario "${user.full_name}"? Podrá ingresar al sistema nuevamente.`,
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
          this.snackBar.open('Usuario activado.', 'Cerrar', { duration: 3000 });
        },
        error: () => this.snackBar.open('No se pudo activar.', 'Cerrar', { duration: 5000 }),
      });
    });
  }
}
