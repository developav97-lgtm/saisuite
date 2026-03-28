/**
 * SaiSuite — ResourceCapacityComponent (Feature #4)
 * CRUD de capacidades semanales de usuarios.
 * Se integra como mat-expansion-panel en el tab "Equipo" de ProyectoDetail.
 */
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  input,
  signal,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ResourceService } from '../../../services/resource.service';
import { AdminService } from '../../../../admin/services/admin.service';
import { AdminUser } from '../../../../admin/models/admin.models';
import { ResourceCapacity } from '../../../models/resource.model';
import { ConfirmDialogComponent } from '../../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ResourceCapacityFormComponent } from './resource-capacity-form.component';

@Component({
  selector: 'app-resource-capacity',
  templateUrl: './resource-capacity.component.html',
  styleUrl: './resource-capacity.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
    MatProgressBarModule,
    MatDialogModule,
  ],
})
export class ResourceCapacityComponent implements OnInit {
  readonly proyectoId = input<string | null>(null);

  private readonly resourceService = inject(ResourceService);
  private readonly adminService    = inject(AdminService);
  private readonly dialog          = inject(MatDialog);
  private readonly snackBar        = inject(MatSnackBar);

  readonly loading    = signal(false);
  readonly capacities = signal<ResourceCapacity[]>([]);
  readonly users      = signal<AdminUser[]>([]);

  readonly displayedColumns = ['usuario', 'horas_por_semana', 'fecha_inicio', 'fecha_fin', 'acciones'];

  ngOnInit(): void {
    this.loadUsers();
    this.loadCapacities();
  }

  loadCapacities(): void {
    this.loading.set(true);
    this.resourceService.listCapacities().subscribe({
      next: (data) => {
        this.capacities.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error al cargar capacidades.', 'Cerrar', {
          duration: 4000, panelClass: ['snack-error'],
        });
      },
    });
  }

  private loadUsers(): void {
    this.adminService.listUsers().subscribe({
      next: (data) => this.users.set(data),
      error: () => { /* silencioso — lista de usuarios no crítica */ },
    });
  }

  openForm(capacity?: ResourceCapacity): void {
    const ref = this.dialog.open(ResourceCapacityFormComponent, {
      data: { capacity, users: this.users() },
      width: '480px',
      disableClose: false,
    });
    ref.afterClosed().subscribe((saved: boolean) => {
      if (saved) this.loadCapacities();
    });
  }

  confirmDelete(capacity: ResourceCapacity): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Eliminar capacidad',
        message: `¿Eliminar la capacidad de "${capacity.usuario_nombre}"?`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
      width: '400px',
    });
    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.resourceService.deleteCapacity(capacity.id).subscribe({
        next: () => {
          this.snackBar.open('Capacidad eliminada.', 'Cerrar', {
            duration: 3000, panelClass: ['snack-success'],
          });
          this.loadCapacities();
        },
        error: () => {
          this.snackBar.open('Error al eliminar la capacidad.', 'Cerrar', {
            duration: 5000, panelClass: ['snack-error'],
          });
        },
      });
    });
  }
}
