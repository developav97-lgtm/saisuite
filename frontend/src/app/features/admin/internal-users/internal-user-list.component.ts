import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialog } from '@angular/material/dialog';
import { InternalUsersService, InternalUser } from '../services/internal-users.service';
import { ToastService } from '../../../core/services/toast.service';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-internal-user-list',
  templateUrl: './internal-user-list.component.html',
  styleUrl: './internal-user-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatChipsModule, MatTooltipModule, MatProgressBarModule,
  ],
})
export class InternalUserListComponent implements OnInit {
  private readonly service = inject(InternalUsersService);
  private readonly router  = inject(Router);
  private readonly dialog  = inject(MatDialog);
  private readonly toast   = inject(ToastService);

  readonly loading = signal(false);
  readonly users   = signal<InternalUser[]>([]);

  readonly columns = ['nombre', 'email', 'tipo', 'estado', 'acciones'];

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.service.list().subscribe({
      next: list => { this.users.set(list); this.loading.set(false); },
      error: () => { this.toast.error('Error al cargar usuarios internos'); this.loading.set(false); },
    });
  }

  tipoLabel(u: InternalUser): string {
    return u.is_superadmin ? 'Super Admin' : 'Soporte';
  }

  tipoColor(u: InternalUser): 'primary' | 'accent' {
    return u.is_superadmin ? 'primary' : 'accent';
  }

  crear(): void {
    this.router.navigate(['/admin/usuarios-internos/nuevo']);
  }

  editar(u: InternalUser): void {
    this.router.navigate(['/admin/usuarios-internos', u.id]);
  }

  toggleActive(u: InternalUser): void {
    const action = u.is_active ? 'desactivar' : 'activar';
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: `${u.is_active ? 'Desactivar' : 'Activar'} usuario`,
        message: `¿Deseas ${action} a "${u.full_name || u.email}"?`,
        confirmText: u.is_active ? 'Desactivar' : 'Activar',
        confirmColor: u.is_active ? 'warn' : 'primary',
      },
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.service.update(u.id, { is_active: !u.is_active }).subscribe({
        next: updated => {
          this.users.update(list => list.map(x => x.id === updated.id ? updated : x));
          this.toast.success(`Usuario ${u.is_active ? 'desactivado' : 'activado'}`);
        },
        error: () => this.toast.error('Error al actualizar usuario'),
      });
    });
  }
}
