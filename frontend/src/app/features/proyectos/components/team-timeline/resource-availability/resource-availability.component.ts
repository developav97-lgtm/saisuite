/**
 * SaiSuite — ResourceAvailabilityComponent (Feature #4)
 * CRUD de ausencias y disponibilidad de usuarios (vacaciones, incapacidades, etc.)
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
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ResourceService } from '../../../services/resource.service';
import { AdminService } from '../../../../admin/services/admin.service';
import { AdminUser } from '../../../../admin/models/admin.models';
import { ResourceAvailability, AVAILABILITY_TYPE_LABELS } from '../../../models/resource.model';
import { ConfirmDialogComponent } from '../../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ResourceAvailabilityFormComponent } from './resource-availability-form.component';

// ResourceAvailabilityFormComponent is opened via MatDialog.open(), not used in template.

@Component({
  selector: 'app-resource-availability',
  templateUrl: './resource-availability.component.html',
  styleUrl: './resource-availability.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
    MatProgressBarModule,
    MatChipsModule,
    MatDialogModule,
  ],
})
export class ResourceAvailabilityComponent implements OnInit {
  readonly proyectoId = input<string | null>(null);

  private readonly resourceService = inject(ResourceService);
  private readonly adminService    = inject(AdminService);
  private readonly dialog          = inject(MatDialog);
  private readonly snackBar        = inject(MatSnackBar);

  readonly loading        = signal(false);
  readonly availabilities = signal<ResourceAvailability[]>([]);
  readonly users          = signal<AdminUser[]>([]);

  readonly AVAILABILITY_TYPE_LABELS = AVAILABILITY_TYPE_LABELS;

  readonly displayedColumns = ['usuario', 'tipo', 'fecha_inicio', 'fecha_fin', 'descripcion', 'estado', 'acciones'];

  ngOnInit(): void {
    this.loadUsers();
    this.loadAvailabilities();
  }

  loadAvailabilities(): void {
    this.loading.set(true);
    this.resourceService.listAvailabilities().subscribe({
      next: (data) => {
        this.availabilities.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error al cargar ausencias.', 'Cerrar', {
          duration: 4000, panelClass: ['snack-error'],
        });
      },
    });
  }

  private loadUsers(): void {
    this.adminService.listUsers().subscribe({
      next: (res) => this.users.set(res.results),
      error: () => { /* silencioso */ },
    });
  }

  openForm(): void {
    const ref = this.dialog.open(ResourceAvailabilityFormComponent, {
      data: { users: this.users() },
      width: '520px',
      disableClose: false,
    });
    ref.afterClosed().subscribe((saved: boolean) => {
      if (saved) this.loadAvailabilities();
    });
  }

  confirmDelete(availability: ResourceAvailability): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Eliminar ausencia',
        message: `¿Eliminar la ausencia de "${availability.usuario_nombre}" (${availability.tipo_display})?`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
      width: '400px',
    });
    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.resourceService.deleteAvailability(availability.id).subscribe({
        next: () => {
          this.snackBar.open('Ausencia eliminada.', 'Cerrar', {
            duration: 3000, panelClass: ['snack-success'],
          });
          this.loadAvailabilities();
        },
        error: () => {
          this.snackBar.open('Error al eliminar la ausencia.', 'Cerrar', {
            duration: 5000, panelClass: ['snack-error'],
          });
        },
      });
    });
  }
}
